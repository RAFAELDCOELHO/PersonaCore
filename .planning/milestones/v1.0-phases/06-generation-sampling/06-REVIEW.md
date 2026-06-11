---
phase: 06-generation-sampling
reviewed: 2026-06-06T00:00:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - src/personacore/generation/__init__.py
  - src/personacore/generation/sampling.py
  - src/personacore/generation/core.py
  - src/personacore/generation/text.py
  - tests/test_generation.py
  - tests/test_generation_text.py
findings:
  critical: 1
  warning: 4
  info: 3
  total: 8
status: issues_found
---

# Phase 6: Code Review Report

**Reviewed:** 2026-06-06
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Phase 6 ships the generation toolkit: pure logit transforms (`sampling.py`), the shared
`generate`/`collect` decode core (`core.py`), and the `str->str` streaming wrapper
(`text.py`). The architecture is clean — single decode path, seed-isolated RNG, defensive
`.clone()` in the filters, strict-UTF-8 cumulative-buffer streaming, and a DoS cap on
`max_new_tokens`. The top-p nucleus math and scatter-back-to-original-order are correct
(verified against unsorted logits and the floating-point boundary at p=0.8/p=1.0).

However the review surfaced one crashing input-validation gap and one genuinely flaky test.

- **BLOCKER:** `top_k=0` (and any `top_k <= 0`) crashes `next_token` with an `IndexError`/
  `RuntimeError` from `torch.topk`. `next_token` guards only `top_k is not None`, never the
  value. A demo/eval caller passing `top_k=0` to mean "disabled" hard-crashes generation.
- **WARNING (reproduced live):** `test_past_block_size_no_crash` is order-dependent and
  failed during this review. It builds an *unseeded* tiny model and asserts an exact output
  length, which only holds if the random argmax never lands on `eos_id`. The author already
  fixed this exact failure mode in `test_output_shape` (`torch.manual_seed(1)` with a comment
  about "perturbed global RNG") but left the twin bug here.

The cross-boundary contracts were checked against the real `GPT.forward` (`(B,T,V)` logits +
`assert T <= block_size`) and the real `BPETokenizer.encode/decode` (strict UTF-8 raising
`UnicodeDecodeError` on partial multi-byte) — both match the wrapper's assumptions.

## Critical Issues

### CR-01: `top_k <= 0` crashes generation (unvalidated sampling parameter)

**File:** `src/personacore/generation/sampling.py:29-39`, `:83-84`
**Issue:** `next_token` enables top-k whenever `top_k is not None`:
```python
if top_k is not None:
    logits = top_k_filter(logits, top_k)
```
`top_k_filter` then calls `torch.topk(logits, k)`. With `k == 0`, `v` is empty and
`v[:, [-1]]` raises `IndexError: index is out of bounds for dimension with size 0`; with
`k < 0`, `torch.topk` raises `RuntimeError`. Both were reproduced on torch 2.7.1. `top_k=0`
is a common idiom for "top-k disabled" and threads straight through `generate` →
`generate_text` → `next_token`, so a single bad demo/eval argument crashes the whole stream
mid-generation (the generator raises inside the `for` loop, not at call time).
**Fix:** Treat non-positive `top_k` as "disabled" at the `next_token` guard (and/or clamp in
`top_k_filter`):
```python
if top_k is not None and top_k > 0:
    logits = top_k_filter(logits, top_k)
```
Optionally also reject negative values explicitly with a `ValueError` so a typo surfaces as a
clear message rather than a deep torch traceback.

## Warnings

### WR-01: Flaky, order-dependent test `test_past_block_size_no_crash`

**File:** `tests/test_generation.py:128-135`
**Issue:** The test constructs an **unseeded** `_tiny_model()` and asserts
`out.shape[1] == prompt.shape[1] + n` (exact length). The untrained model's greedy argmax can
land on `eos_id` (15), in which case `generate` stops early and the assertion fails. This was
**reproduced during review**: running `pytest tests/test_generation.py
tests/test_generation_text.py` produced `....F........` with
`assert 3 == (3 + 12)` — the model emitted EOS on step 1 because a prior test's model
construction had perturbed the global RNG. The test passes in isolation and in some orderings,
which is precisely the "global-RNG flakiness (Pitfall 2)" the author called out and fixed in
`test_output_shape` (line 149, `torch.manual_seed(1)`) — but the identical guard is missing
here.
**Fix:** Seed before constructing the model, mirroring `test_output_shape`:
```python
def test_past_block_size_no_crash():
    torch.manual_seed(1)  # avoid argmax landing on eos_id under a perturbed global RNG
    model = _tiny_model()
    ...
```
Better still, force the forward (as `test_eos_stop` does) so the assertion does not depend on
random weights at all.

### WR-02: `top_p` accepts out-of-range values and silently degrades

**File:** `src/personacore/generation/sampling.py:42-60`, `:85-86`
**Issue:** `next_token` enables top-p on `top_p is not None` with no range check. Verified
behavior: `p <= 0` collapses the nucleus to the single top-1 token (silently near-greedy);
`p > 1` keeps the entire vocabulary (top-p effectively a no-op). Neither raises, so a
mis-scaled value (e.g. passing a percentage `80` instead of `0.8`) silently produces wrong
sampling with no signal. Less severe than CR-01 (no crash, no data loss) but it masks caller
bugs in a sampling path where wrong behavior is hard to notice.
**Fix:** Validate at the `next_token` boundary:
```python
if top_p is not None:
    if not (0.0 < top_p <= 1.0):
        raise ValueError(f"top_p must be in (0, 1], got {top_p!r}")
    logits = top_p_filter(logits, top_p)
```

### WR-03: `eos_id=None` makes `generate` never stop (silent runaway)

**File:** `src/personacore/generation/core.py:51,65-66`
**Issue:** `eid = eos_id if eos_id is not None else model.config.eos_id`. If a caller passes
`eos_id=None` *and* `model.config.eos_id` is `None`, then `eid is None`, and `tok == eid` is
`int == None` → always `False`, so the EOS-stop never fires; generation only halts at
`max_new_tokens`. Today `ModelConfig.eos_id` defaults to a real int (8184), so this is latent
rather than live — but the contract "stop on EOS" is silently void with no diagnostic if a
config ever carries `eos_id=None`. The DoS cap in `text.py` bounds the runaway only for the
demo path; `core.generate`/`collect` (used by Phase-7 eval) have no such cap.
**Fix:** Assert `eid is not None` once before the loop:
```python
if eid is None:
    raise ValueError("eos_id is required (pass eos_id= or set model.config.eos_id)")
```

### WR-04: `max_new_tokens` is not validated as an integer

**File:** `src/personacore/generation/text.py:67-70`; `src/personacore/generation/core.py:53`
**Issue:** `generate_text` checks `max_new_tokens <= 0 or > cap` but not the type. A float
(e.g. `2.5`) passes the bound check, then in `core.generate` `range(max_new_tokens)` raises
`TypeError: 'float' object cannot be interpreted as an integer` deep inside the generator —
a confusing failure far from the `generate_text` entry point that nominally "validates" the
argument. The docstring advertises this as the validated DoS guard, so the type gap undercuts
that contract.
**Fix:** Tighten the guard:
```python
if not isinstance(max_new_tokens, int) or max_new_tokens <= 0 or max_new_tokens > max_new_tokens_cap:
    raise ValueError(...)
```

## Info

### IN-01: `top_p` docstring/comment contradicts itself on boundary semantics

**File:** `src/personacore/generation/sampling.py:42-58`
**Issue:** The docstring says "mask tokens once the cumulative mass has EXCEEDED `p`", the
inline comment at line 52 says "`>=` so a token landing EXACTLY on the cumulative-`p` boundary
closes the nucleus (it does not pull in the next token)", and the comment at line 56 says
"keep the boundary token". The three phrasings are individually defensible but read as
conflicting; the actual code (>= then shift-right) is correct and matches the test, but the
prose costs a reader real time to reconcile. **Fix:** Collapse to one sentence: "Keep every
token up to and including the first whose running cumulative softmax reaches `p`; never mask
the top-1 token."

### IN-02: `collect` rebuilds a 1x1 tensor per step from a Python int

**File:** `src/personacore/generation/core.py:78-79`
**Issue:** `generate` already appends `next_id` (a `(1,1)` tensor) to its internal `idx`, then
yields `int(next_id)`; `collect` throws that internal tensor away and reconstructs
`torch.tensor([[tok]], ...)` each step. Correct, but the round-trip
tensor→int→tensor is redundant. Not a bug (dtype/device are preserved explicitly) and not in
v1 perf scope — noted only as a readability/duplication smell. **Fix:** If a refactor touches
this, have `generate` yield the `(1,1)` tensor and let `collect` `cat` it directly, or keep
`collect` as the sole owner of the running tensor.

### IN-03: Bare `int(next_id)` assumes a single-element tensor

**File:** `src/personacore/generation/core.py:64`
**Issue:** `tok = int(next_id)` relies on `next_token` always returning exactly one element
(`(1,1)`). True today for both the greedy `argmax(keepdim=True)` and `multinomial(num_samples=1)`
paths, so this is safe — but it is an implicit single-sequence/`num_samples=1` invariant that
would raise an opaque "only one element tensors can be converted" error if either path ever
changed. **Fix:** Either document the invariant inline or use `next_id.item()` (same effect,
clearer single-element intent).

---

_Reviewed: 2026-06-06_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
