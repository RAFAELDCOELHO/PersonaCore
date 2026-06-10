---
phase: 08-demo-writeup
reviewed: 2026-06-10T21:38:33Z
depth: standard
files_reviewed: 11
files_reviewed_list:
  - scripts/export_slim.py
  - scripts/demo_app.py
  - src/personacore/checkpoint.py
  - src/personacore/generation/text.py
  - src/personacore/generation/__init__.py
  - tests/test_slim_checkpoint.py
  - tests/test_demo_callback.py
  - pyproject.toml
  - demo.ipynb
  - docs/REPORT.md
  - README.md
findings:
  critical: 1
  warning: 4
  info: 8
  total: 13
status: issues_found
---

# Phase 08: Code Review Report

**Reviewed:** 2026-06-10T21:38:33Z
**Depth:** standard
**Files Reviewed:** 11
**Status:** issues_found

## Summary

Phase 8 ships the slim inference checkpoint (`export_slim`/`load_slim`), the offline Gradio
demo, the executed results notebook, the technical report, and the README front door. The
security posture of the headline deliverable is sound and was verified directly:
`load_slim` is a genuine `weights_only=True` choke point, the slim artifact round-trips the
restricted unpickler (proved by `test_export_strips_training_state` loading raw with
`weights_only=True`), the demo's offline guarantee holds against the installed gradio 5.50.0
source (`GRADIO_ANALYTICS_ENABLED` gates `version_check()` at
`gradio/analytics.py:46,107`), `share=False` binds localhost, and the gradio examples
list-of-lists comment matches the actual `ChatInterface` implementation. The full test suite
was executed during review: 130 passed, 1 skipped in 70s.

One Critical defect was found and **empirically confirmed by measurement on the shipped
artifact**: the demo can crash on settings its own UI offers, because the frozen production
tokenizer can only decode 547 of the model's 8192 token ids (the BPE trainer itself warns
`corpus exhausted: learned 283 of 7928 requested merges; vocab_size=8192 has 7645 dead
ids`), and the streaming wrapper only catches `UnicodeDecodeError` while unknown ids raise
plain `ValueError`. At temperature 1.5 with top-k disabled — both reachable via the demo's
sliders — the measured probability of sampling an undecodable id within one 400-token
generation is ~29%. The same 7645-dead-id fact also undercuts the "vocabulary 8192" claim
repeated in README and REPORT (Warning).

## Critical Issues

### CR-01: Demo crashes mid-generation at in-UI slider settings — undecodable token ids raise uncaught `ValueError`

**File:** `scripts/demo_app.py:97,109-110` / `src/personacore/generation/text.py:86-89` / `src/personacore/tokenizer/bpe.py:208`

**Issue:** The model samples over all 8192 vocab ids, but the frozen production tokenizer
(`artifacts/tokenizer.json`) contains only 283 merges — its decodable id set is 547 ids
(0–538 byte/merge ids + 8184–8191 specials). For any other id, `BPETokenizer.decode` raises
`ValueError(f"unknown token id: {idx}")` (bpe.py:208). The streaming wrapper's per-step
decode catches **only** `UnicodeDecodeError` (text.py:88-89, the partial-glyph case), so the
unknown-id `ValueError` propagates out of `generate_text`, through
`generate_text_cumulative`, and kills the `tell_story` callback — the user's message errors
out in the Gradio UI.

This is reachable through the demo's own controls: the Top-k slider explicitly offers
`0 = disabled` (demo_app.py:97,110), and the Temperature slider goes to 1.5
(demo_app.py:109). Measured on the shipped `model_slim.pt` + frozen tokenizer (one forward
pass on the first README example prompt):

| settings | undecodable mass / step | ~P(crash in 400 tokens) |
| --- | --- | --- |
| temp 0.8, top-k off | 9.3e-10 | 3.7e-07 |
| temp 1.0, top-k off | 3.5e-07 | 1.4e-04 |
| temp 1.5, top-k off | 8.5e-04 | **2.9e-01** |

At the slider extremes, roughly 1 in 3 long generations crashes. The default settings
(temp 0.8, top-k 50) are safe — the top-k filter never admits a dead id — which is why
the committed demo GIF and notebook never hit it. The notebook is also safe (temp 0.8
and/or top-p 0.95). Only the live demo is exposed.

**Fix:** Mask the tokenizer-undecodable ids out of the logits before sampling, so the dead
ids are unreachable regardless of slider settings. Smallest principled change — thread an
optional `forbid_ids` mask through the sampling path and pass it from the demo:

```python
# sampling.py — next_token(..., forbid_ids=None):
if forbid_ids is not None:
    logits = logits.masked_fill(forbid_ids, float("-inf"))   # before temperature/top-k/top-p
# (apply in the greedy branch too)

# core.generate / text.generate_text: accept and pass through forbid_ids=...

# demo_app.build_demo(), after tok = from_json(...):
decodable = set(tok.vocab) | set(tok.special_tokens.values())
forbid = torch.tensor(
    [i not in decodable for i in range(model.config.vocab_size)]
).unsqueeze(0)  # (1, vocab) bool mask
# tell_story: generate_text_cumulative(..., forbid_ids=forbid)
```

Do **not** fix this by catching `ValueError` in `text.py` — that would silently truncate the
story and also swallow genuine decode defects the strict-decode design (WR-03 lineage) is
meant to surface. Add a regression test that forces an undecodable id through a stub model
and asserts generation either masks it or fails loudly with a clear message.

## Warnings

### WR-01: "Vocabulary 8192" claim contradicts the shipped artifact — 7645 of 8192 ids are dead

**File:** `README.md:29-30` / `docs/REPORT.md:34-35,49-58,357-359`

**Issue:** README ("Byte-level BPE tokenizer trained from scratch — vocabulary 8192") and
REPORT ("vocabulary 8192", "fix `vocab_size=8192` ... before any model was sized",
Results: "vocabulary 8192") present 8192 as the vocabulary. The frozen production
`artifacts/tokenizer.json` contains 283 merges: 547 live ids total. The project's own BPE
trainer warns about exactly this (`corpus exhausted: learned 283 of 7928 requested merges;
vocab_size=8192 has 7645 dead ids` — emitted during this review's test run). Consequences
the report never states: ~2.93M of the headline 13,891,584 parameters are embedding rows
for tokens that can never occur in training data or be decoded, and the model's effective
vocabulary is 547. For a report whose stated bar is honest, auditable framing (it ships
denominators with every perplexity), this is a material omission — and it is the same fact
that produces CR-01.

**Fix:** State the effective vocabulary honestly wherever 8192 is claimed, e.g.:
"vocab table 8192 (547 ids live: 256 bytes + 283 learned merges + 8 specials; the bounded
training corpus exhausted its mergeable pairs — the remaining rows are reserved capacity)."
Add one sentence to the parameter-count discussion acknowledging the dead embedding rows.

### WR-02: `export_slim` crashes with opaque `TypeError` when the full checkpoint has `val_loss=None`

**File:** `src/personacore/checkpoint.py:137`

**Issue:** `"val_loss": float(full["val_loss"])` assumes `val_loss` is numeric, but
`save_checkpoint`'s own signature defaults `val_loss=None` (checkpoint.py:44). Any full
checkpoint written without an explicit `val_loss` (e.g., a future M2 caller using the
open-dict API, or an ad-hoc save) makes `export_slim` die with
`TypeError: float() argument must be ... not 'NoneType'` — no pointer to the actual
problem. The current training loop always passes a value, so `best.pt` works today, but the
exporter's contract is broader than the one caller.

**Fix:**
```python
val_loss = full.get("val_loss")
slim = {
    ...
    "val_loss": float(val_loss) if val_loss is not None else None,
}
```
(`None` survives `weights_only=True` loading, so the slim contract is preserved.)

### WR-03: README quickstart fails verbatim — no clone step before `pip install -e .`

**File:** `README.md:48-63`

**Issue:** The "Run the demo" block starts at `python3.11 -m venv .venv` and then runs
`pip install -e ".[cpu,demo]"` and `gh release download m1-demo-v1` — both of which require
already being inside a checkout of the repository (editable install of `.`; `gh` infers the
repo from the git remote). A newcomer following the front-door quickstart from an empty
directory fails at step 1 with no hint. (The release tag `m1-demo-v1` itself could not be
verified from this sandbox — network blocked; confirm it exists and carries
`model_slim.pt` before publishing.)

**Fix:** Add the clone as step 0:
```bash
git clone https://github.com/RAFAELDCOELHO/PersonaCore.git
cd PersonaCore
```

### WR-04: `notebook` extra cannot run the notebook — matplotlib lives only in the `demo` extra

**File:** `pyproject.toml:17-18`

**Issue:** `demo.ipynb` imports `matplotlib` in two cells, but the `notebook` extra ships
only `ipykernel` + `nbconvert`; `matplotlib` is bundled into `demo` (where nothing in
`scripts/demo_app.py` uses it). An environment installed as `.[cpu,notebook]` — the natural
reading of the extras — fails at the `training-curves` cell with `ModuleNotFoundError`. It
works today only if you happen to follow the README's `[cpu,demo]` install.

**Fix:** Add matplotlib to the extra that actually needs it:
```toml
demo = ["gradio>=5,<6"]
notebook = ["ipykernel~=7.3", "nbconvert~=7.17", "matplotlib~=3.10"]
```
(or duplicate `matplotlib~=3.10` in both if the demo extra intends to cover the notebook).

## Info

### IN-01: Stale test count in REPORT

**File:** `docs/REPORT.md:396-397`
**Issue:** "126 passed, 1 skipped" — the suite executed during this review reports
**130 passed, 1 skipped** (the four Phase-8 tests landed after the sentence was written).
**Fix:** Update the count, or phrase it unpinned ("~130 CPU-only tests, suite green") as
README already does.

### IN-02: `best.pt` "159 MB" mixes MiB and MB in the same sentence

**File:** `docs/REPORT.md:318-319`
**Issue:** `best.pt` is 166,808,536 bytes = 166.8 MB (decimal) = 159.1 MiB; the slim file in
the same sentence is quoted decimal ("~55.6 MB" = 55,601,269 bytes). One unit base per
document.
**Fix:** "the full training checkpoint `best.pt` (167 MB, ...)".

### IN-03: Dead `except ImportError: GPT = None` guard with no skip

**File:** `tests/test_demo_callback.py:26-29`
**Issue:** If the import ever failed, `GPT = None` would make every test crash with
`TypeError: 'NoneType' object is not callable` instead of skipping — there is no
`pytest.mark.skipif(GPT is None, ...)` anywhere. The guard is vestigial ("model package
ships in Phase 4" — it shipped) and copied from `tests/test_generation_text.py:22-23`,
which has the same dead pattern.
**Fix:** Delete the try/except (import directly), or add
`pytestmark = pytest.mark.skipif(GPT is None, reason="model package not built")`.

### IN-04: Notebook settings tour shows two byte-identical outputs with no explanation

**File:** `demo.ipynb` (cell `settings-tour` outputs)
**Issue:** The committed outputs for "temperature=0.8" and "temperature=0.8, top_k=50" are
identical for all 120 tokens. Threading was verified correct during review (top_k reaches
`next_token` → `top_k_filter`); the cause is statistical — at temp 0.8 the mass outside the
top-50 is ~1e-9/step, so filtering almost never alters the seeded multinomial draw. A
reader of a tour whose stated point is "how each sampling choice changes the text" will
suspect a bug.
**Fix:** Add one markdown line ("top-k 50 leaves this peaked distribution effectively
unchanged at temp 0.8 — identical output under the same seed is the expected result"), or
demo top-k at a higher temperature where it visibly bites.

### IN-05: Trailing partial multi-byte glyph is silently dropped at end of stream

**File:** `src/personacore/generation/text.py:86-89`
**Issue:** If generation ends (max_new_tokens, or EOS) while `buffer_ids` ends mid-glyph,
the held bytes never surface — the final character is silently lost. Correct trade-off for
a strict decoder, but undocumented; D-06 describes only the mid-stream case.
**Fix:** One docstring sentence noting the terminal partial-glyph drop is intentional.

### IN-06: `save_checkpoint` `**extra` can silently shadow reserved keys

**File:** `src/personacore/checkpoint.py:58-77`
**Issue:** `**extra` unpacks last in the dict literal, so `extra={"model": ...}` (or
`"rng"`, `"step"`, ...) silently replaces the real training state. The M2 EWC seam invites
arbitrary keys, making an accidental collision plausible.
**Fix:** `reserved = ckpt.keys() & extra.keys(); if reserved: raise ValueError(...)` before
merging.

### IN-07: cwd-dependent paths make the real-artifact test skip silently

**File:** `tests/test_slim_checkpoint.py:41-42,141`
**Issue:** `REAL_SLIM = pathlib.Path("checkpoints/model_slim.pt")` is resolved at collection
time relative to the invocation cwd. Run pytest from anywhere but the repo root and
`test_real_slim_artifact_generates_on_cpu` silently skips even when the artifact exists
(and `TOKENIZER_PATH` would 404 in the others). Matches existing project convention
(`tests/test_best_ckpt.py:31`), so flagged for reliability, not style.
**Fix:** Anchor to the test file:
`REPO = pathlib.Path(__file__).resolve().parent.parent; REAL_SLIM = REPO / "checkpoints/model_slim.pt"`.

### IN-08: `load_slim` assumes the payload is a dict

**File:** `src/personacore/checkpoint.py:150-151`
**Issue:** `loaded.get("schema_version")` raises `AttributeError` if a foreign/corrupt file
contains a bare tensor or list (all loadable under `weights_only=True`), bypassing the
designed `ValueError` with its re-export hint — the one validation path strangers' downloads
go through.
**Fix:** `if not isinstance(loaded, dict) or loaded.get("schema_version") != SLIM_SCHEMA_VERSION: raise ValueError(...)`.

---

_Reviewed: 2026-06-10T21:38:33Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
