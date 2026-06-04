---
phase: 02-from-scratch-bpe-tokenizer
reviewed: 2026-06-04T00:00:00Z
depth: standard
files_reviewed: 16
files_reviewed_list:
  - src/personacore/config.py
  - src/personacore/tokenizer/__init__.py
  - src/personacore/tokenizer/bpe.py
  - src/personacore/tokenizer/io.py
  - src/personacore/tokenizer/patterns.py
  - src/personacore/tokenizer/special.py
  - scripts/train_tokenizer.py
  - pyproject.toml
  - requirements.txt
  - tests/test_config.py
  - tests/test_tokenizer_train.py
  - tests/test_tokenizer_roundtrip.py
  - tests/test_tokenizer_special.py
  - tests/test_tokenizer_io.py
  - tests/test_tokenizer_oracle.py
  - tests/fixtures/tricky_strings.py
findings:
  critical: 1
  warning: 5
  info: 4
  total: 10
status: issues_found
---

# Phase 2: Code Review Report

**Reviewed:** 2026-06-04
**Depth:** standard
**Files Reviewed:** 16
**Status:** issues_found

## Summary

The from-scratch byte-level BPE tokenizer is, in its happy path, correct and well-engineered: byte-level base-256 coverage gives exact `decode(encode(x)) == x` round-trips, the merge train loop uses a total-order tie-break for determinism, special tokens are split atomically before BPE, and the JSON freeze format is genuinely data-only (no pickle/torch on the artifact load path — the stated security divergence from `checkpoint.py` holds). The tiktoken oracle is correctly confined to tests and a guard test enforces no runtime leak. All of this was verified by running the tokenizer directly.

The defects cluster on the **artifact load path (`io.py`)**, which is explicitly billed in its own docstring as a security/validation boundary (threats T-02-05/T-02-06, ASVS V5). That boundary is weaker than advertised: the schema-version check is an `assert` (silently removed under `python -O`), `special_tokens` ids and `eos_id` are not range-validated at all (only `merges` are), missing keys surface as raw `KeyError`, and `decode` can silently shadow a special id with a colliding merge id. These do not bite the committed production artifact because the locked id layout (specials 8184-8191, merges 256-8183) avoids the collision class, but `from_json` accepts arbitrary third-party/edited artifacts and does not enforce that layout — which is the exact scenario the validation was written to defend.

The single Critical is the `assert`-based schema guard, because it is the documented integrity control and it is trivially and silently bypassed in any optimized interpreter run.

## Critical Issues

### CR-01: Schema-version integrity check uses `assert` — silently bypassed under `python -O`

**File:** `src/personacore/tokenizer/io.py:55`
**Issue:** `from_json` enforces its schema-version contract with `assert d["schema_version"] == SCHEMA_VERSION`. Python strips all `assert` statements when run with `-O` or `PYTHONOPTIMIZE=1`. The io.py docstring explicitly markets this line as threat-mitigation T-02-06 ("asserts the schema version") and the load path as a validation boundary for swappable/editable artifacts. An `assert` is the wrong tool for a security/integrity control. Verified directly:

```
$ python    -c "from_json(schema_version=999 artifact)"  -> AssertionError (guard fires)
$ python -O -c "from_json(schema_version=999 artifact)"  -> LOADED (guard silently skipped)
```

A future/incompatible or tampered artifact would load without complaint, then misbehave downstream (wrong merge semantics, wrong vocab assumptions) with no error pointing at the cause.

**Fix:** Replace the `assert` with an explicit raise that survives optimization, and treat a missing key as a validation failure rather than a `KeyError`:
```python
schema = d.get("schema_version")
if schema != SCHEMA_VERSION:
    raise ValueError(
        f"tokenizer schema mismatch: artifact={schema!r}, expected={SCHEMA_VERSION}"
    )
```

## Warnings

### WR-01: `from_json` does not validate `special_tokens` ids or `eos_id` — only `merges` are range-checked

**File:** `src/personacore/tokenizer/io.py:57-71`
**Issue:** The V5 input-validation loop checks `0 <= token_id < vocab_size` only for the three members of each merge triple. `special_tokens` ids and `eos_id` are loaded verbatim with no validation. Verified: an artifact with `special_tokens={"<|endoftext|>": 999999}` and `eos_id=-5` loads cleanly and produces a tokenizer with `eos_id == -5`. A negative or out-of-range `eos_id` propagates into `ModelConfig`/checkpoints and would index the embedding table incorrectly downstream (Phase 3/4 consume `eos_id` for model sizing and generation stop conditions). This directly undercuts the "reject a malformed or out-of-range swapped artifact" guarantee in the io.py docstring.

**Fix:** Extend the range check to specials and EOS, and assert the locked layout invariant:
```python
for tid in d["special_tokens"].values():
    if not (0 <= tid < vocab_size):
        raise ValueError(f"special token id {tid} outside [0, {vocab_size})")
if not (0 <= d["eos_id"] < vocab_size):
    raise ValueError(f"eos_id {d['eos_id']} outside [0, {vocab_size})")
if d["eos_id"] not in d["special_tokens"].values():
    raise ValueError("eos_id is not one of the declared special-token ids")
```

### WR-02: `decode` resolves an id against `vocab` before `special_tokens` — a colliding special id is silently shadowed

**File:** `src/personacore/tokenizer/bpe.py:179-185`
**Issue:** `decode` checks `if idx in self.vocab` first, then `inverse_special`. If a special id ever overlaps a merge/byte id, the special is silently decoded as merge bytes — the round-trip for that special is corrupted with no error. Verified by constructing a `frozen()` tokenizer with `special_tokens={"<|endoftext|>": 256}` overlapping merge id 256: `decode([256])` returns `'ab'` instead of the EOS literal. The committed artifact avoids this because the locked layout separates the ranges, but `frozen()`/`from_json` accept any `special_tokens` map and never enforce non-overlap, so the invariant is unguarded. This is a latent data-loss path for an external/edited artifact and a fragility for anyone who reuses `frozen()` with a different layout.

**Fix:** Resolve specials first (they are the authoritative atomic ids), or assert disjointness at construction time. Preferred — check specials first in `decode`:
```python
for idx in ids:
    if idx in inverse_special:
        parts.append(inverse_special[idx].encode("utf-8"))
    elif idx in self.vocab:
        parts.append(self.vocab[idx])
    else:
        raise ValueError(f"unknown token id: {idx}")
```
Additionally, validate `set(special_tokens.values()).isdisjoint(vocab)` in `frozen()`.

### WR-03: `decode` uses `errors="replace"`, which masks genuine corruption instead of failing loudly

**File:** `src/personacore/tokenizer/bpe.py:186`
**Issue:** `b"".join(parts).decode("utf-8", errors="replace")` is documented as a "never-triggered safety net." But its only effect is to hide bugs: a malformed id stream, a truncated merge sequence, or a mis-decoded special would produce U+FFFD replacement characters and a silently wrong string rather than an exception. For a from-scratch tokenizer whose entire correctness claim is exact round-trip, a silent lossy fallback is the wrong default — it converts a detectable defect into invisible data loss. The round-trip tests pass precisely because the net never fires on valid input, so this fallback buys nothing on the happy path and costs detectability on the unhappy path.

**Fix:** Use `errors="strict"` (the default) so any non-round-trippable byte stream raises `UnicodeDecodeError`:
```python
return b"".join(parts).decode("utf-8")
```
If a lenient mode is ever wanted, make it an explicit opt-in parameter.

### WR-04: `train()` sets `vocab_size` to the requested value even when far fewer merges were learned, leaving a large dead id range

**File:** `src/personacore/tokenizer/bpe.py:104-116`; artifact: `artifacts/tokenizer.json`
**Issue:** When the corpus is exhausted of mergeable pairs (`if not stats: break`), the loop stops early but `self.vocab_size = vocab_size` is still set to the full request. The committed production artifact reports `vocab_size: 8192` while learning only **283 merges** (max merge id 538), leaving ids 539-8183 as permanently dead embedding rows. This is documented as intentional in 02-03-SUMMARY, but it means the shipped "production" tokenizer was trained on the 11.5 KB CI fixture, not a representative corpus — the artifact embeds a near-empty merge table behind a 8192 vocab claim. Phase 5 is contracted to reuse this exact frozen artifact with no retrain, so the model will allocate (and train) ~7650 unused embedding rows. At minimum this should be a loud warning, not a silent acceptance; ideally the production artifact should be regenerated from the documented bounded TinyStories slice before any model is sized around it.

**Fix:** Either (a) regenerate `artifacts/tokenizer.json` from the bounded TinyStoriesV2-GPT4 sample described in `scripts/train_tokenizer.py` so the merge table actually fills toward 8192, or (b) have `train()` emit a warning when `len(merges) < num_merges` so an under-trained artifact is never frozen silently:
```python
if len(merges) < num_merges:
    warnings.warn(
        f"corpus exhausted: learned {len(merges)} of {num_merges} requested merges; "
        f"vocab_size={vocab_size} has {num_merges - len(merges)} dead ids"
    )
```

### WR-05: `encode` treats any `allowed_special` value other than the literal `"all"` as "disable specials" — silent, surprising API

**File:** `src/personacore/tokenizer/bpe.py:139-150`
**Issue:** The only recognized value is the string `"all"`; anything else (a set of allowed names per the minbpe convention, `None`, a typo like `"All"`) silently falls through to encoding the whole string as ordinary bytes — meaning embedded `<|endoftext|>` literals would be byte-split rather than emitted as the atomic EOS id. Because the failure is silent, a caller who mistypes the flag or passes the conventional set form gets document boundaries silently destroyed, which Phase 5 depends on. There is no validation or error for an unrecognized value.

**Fix:** Either support the minbpe set/`"none"` convention explicitly, or reject unknown values:
```python
if allowed_special == "all":
    specials = self.special_tokens
elif allowed_special == "none" or not allowed_special:
    specials = {}
elif isinstance(allowed_special, (set, frozenset)):
    specials = {k: v for k, v in self.special_tokens.items() if k in allowed_special}
else:
    raise ValueError(f"unrecognized allowed_special={allowed_special!r}")
```

## Info

### IN-01: `from_json` raises raw `KeyError` on a malformed artifact missing a required key

**File:** `src/personacore/tokenizer/io.py:53-71`
**Issue:** An artifact missing `schema_version`, `vocab_size`, `merges`, etc. surfaces as a bare `KeyError: 'schema_version'` rather than a descriptive validation error naming the artifact. For a documented validation boundary, the error should identify the problem and the file.
**Fix:** Read required keys via `d.get(...)` with explicit `raise ValueError(f"artifact {path} missing required key '...'")`, or validate the key set up front.

### IN-02: `requires-python = ">=3.10,<3.12"` excludes 3.12, but project docs say "3.10-3.12 ok"

**File:** `pyproject.toml:9`
**Issue:** CLAUDE.md / STACK guidance states Python "3.10-3.12 ok" with 3.11 as the target, but the constraint upper-bounds at `<3.12`, excluding 3.12 entirely. This is a minor consistency gap; if intentional (strict Kaggle 3.11 parity) it is fine, but the inline comment ("Kaggle 3.11 parity") cites D-10 which is about torch wheels, not the Python ceiling.
**Fix:** Confirm intent; if 3.12 is acceptable, widen to `<3.13`. Otherwise correct the comment to explain the deliberate 3.12 exclusion.

### IN-03: `__all__` ordering / public surface mixes data and callables without grouping

**File:** `src/personacore/tokenizer/__init__.py:8-17`
**Issue:** Cosmetic only — `__all__` interleaves the class, pattern constant, special-token data, and io functions. Not a defect; noted for polish since this is a portfolio artifact where the public surface is read by reviewers.
**Fix:** Optional: group as (class, constants, functions) with comments.

### IN-04: `decode` rebuilds `inverse_special` on every call

**File:** `src/personacore/tokenizer/bpe.py:177`
**Issue:** `inverse_special = {idx: name for ...}` is recomputed on each `decode` call. Functionally correct and out of v1 perf scope, but for a frozen tokenizer the inverse map is invariant and could be built once in `__init__`/`frozen()`. Noted only because Phase 5 will call `decode` in a hot loop.
**Fix:** Compute `self.inverse_special` once at construction.

---

## Narrative Findings (AI reviewer)

Positive verifications worth recording (no action needed):

- **No oracle leak in runtime:** confirmed no `tiktoken`/oracle import anywhere under `src/personacore/`; the `recover_merges` adapter lives entirely in `tests/test_tokenizer_oracle.py`. The `test_no_runtime_tiktoken` guard correctly scans `src/personacore/**/*.py`.
- **Freeze path is genuinely data-only:** `io.py` uses stdlib `json` exclusively — no `pickle`, no `torch.load`, no `eval`/`exec`. The artifact cannot execute code on load. This is the stated T-02-05 control and it holds.
- **Determinism holds:** the `max(stats, key=lambda p: (stats[p], p))` tie-break is a total order over (freq, int-tuple); two trains on the same corpus produce byte-identical merge tables (verified by execution).
- **Round-trip holds on the tricky set:** byte-level coverage round-trips emoji/ZWJ, smart quotes, multi-byte scripts, whitespace runs, and embedded `<|endoftext|>` literals exactly (verified); the chunk-join invariant `"".join(chunks).encode() == text.encode()` holds including `\r\n` and whitespace-only inputs.
- **Special-token atomicity holds:** `encode("a<|endoftext|>b")` yields exactly one EOS id; the capturing longest-first split prevents merging across the document separator.

_Reviewed: 2026-06-04_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
