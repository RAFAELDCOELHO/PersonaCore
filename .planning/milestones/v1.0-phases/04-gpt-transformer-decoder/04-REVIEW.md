---
phase: 04-gpt-transformer-decoder
reviewed: 2026-06-05T16:13:23Z
depth: standard
files_reviewed: 11
files_reviewed_list:
  - src/personacore/model/gpt.py
  - src/personacore/model/__init__.py
  - tests/test_gpt_model.py
  - tests/test_gpt_attention_equiv.py
  - tests/test_gpt_layernorm.py
  - tests/test_gpt_weight_tying.py
  - tests/test_gpt_init.py
  - tests/test_gpt_param_count.py
  - tests/test_gpt_causality.py
  - tests/test_gpt_lora_seam.py
  - tests/test_gpt_overfit.py
findings:
  critical: 1
  warning: 4
  info: 3
  total: 8
status: issues_found
---

# Phase 4: Code Review Report

**Reviewed:** 2026-06-05T16:13:23Z
**Depth:** standard
**Files Reviewed:** 11
**Status:** issues_found

## Summary

The from-scratch GPT-2 decoder is well-constructed and the core ML invariants are honored
correctly: weight tying shares the actual `nn.Parameter` (`data_ptr` identity, line 177),
residual-scaled init is applied to BOTH `c_proj` and `fc_out` (lines 171-173), the manual
attention path masks before softmax with `-inf` (lines 99-102), and the hand-rolled LayerNorm
uses population variance (line 48) to match `nn.LayerNorm`. The init ordering (base -> residual
override -> tie) is correct, and the LOCKED `(logits, loss)` contract matches `bigram.py` exactly.

However, there is one BLOCKER: the model has no `block_size` guard, so any sequence longer than
`block_size` crashes on the positional-embedding lookup instead of failing with a clear error or
being handled. Several WARNINGs concern fp16/autocast numerical safety (the hand-rolled LayerNorm
and the manual softmax run in fp16 under the training loop's autocast, where the oracle-matching
guarantees the test suite proves in fp32 no longer hold), and an asymmetry where the `sdpa` branch
ignores `config.dropout` while the manual branch applies it — a latent equivalence/regularization
gap. None of the test files contains a correctness defect.

## Critical Issues

### CR-01: No `block_size` bounds check — sequences longer than `block_size` crash on positional embedding

**File:** `src/personacore/model/gpt.py:188-192`
**Issue:** `forward` unpacks `B, T = idx.shape` and immediately does
`pos = torch.arange(T, device=idx.device)` followed by `self.wpe(pos)`. `wpe` is
`nn.Embedding(config.block_size, config.n_embd)` (line 160). If `T > config.block_size`,
`torch.arange(T)` produces indices `>= block_size`, and the `wpe` lookup is an out-of-bounds
index — on CPU this raises a cryptic `IndexError`/device-assert, and on CUDA it triggers a
non-recoverable `device-side assert triggered` that poisons the whole CUDA context for the rest
of the session (fatal during a long Kaggle run). The causal `tril` buffer is also only
`block_size x block_size` (lines 80-86), so `self.tril[:, :, :T, :T]` would silently slice short
and produce a wrong-shaped mask if it didn't crash on `wpe` first. There is no assertion, no clamp,
and no documented contract that callers must pre-truncate to `block_size`. This is a silent
correctness/availability hazard at inference and generation time.
**Fix:**
```python
def forward(self, idx, targets=None):
    B, T = idx.shape
    assert T <= self.config.block_size, (
        f"sequence length {T} exceeds block_size {self.config.block_size}; "
        f"truncate the context to the last {self.config.block_size} tokens before forward"
    )
    tok_emb = self.wte(idx)
    pos = torch.arange(T, device=idx.device)
    ...
```
A clear assertion converts a fatal CUDA-context kill into an actionable error; the
generation/sampling caller is then responsible for cropping `idx[:, -block_size:]`.

## Warnings

### WR-01: Hand-rolled LayerNorm runs in fp16 under autocast — loses the fp32 oracle-equivalence guarantee

**File:** `src/personacore/model/gpt.py:46-49`
**Issue:** The training loop wraps the forward in `runtime.autocast()` (`training/loop.py:115`),
which on the Kaggle P100 path enables fp16 autocast. `nn.LayerNorm` is on autocast's fp32 cast
list (PyTorch promotes it to fp32 internally for numerical stability), but this hand-rolled
LayerNorm is built from raw `mean`/`var`/`sqrt`/mul ops, which autocast runs in fp16. Computing
the variance and the `1/sqrt(var + eps)` reciprocal in fp16 is exactly the precision-loss case
LayerNorm fp32-promotion exists to avoid; small variances and the `eps=1e-5` term lose significant
bits. The test suite (`test_gpt_layernorm.py`) only proves equivalence to `nn.LayerNorm` in fp32
(`atol=1e-6`), so this divergence is invisible to the gate but real during fp16 training. This is
a numerical-correctness regression relative to the "matches nn.LayerNorm" contract the phase
claims.
**Fix:** Compute the normalization statistics in fp32 regardless of autocast, then cast back:
```python
def forward(self, x):
    dtype = x.dtype
    xf = x.float()
    mean = xf.mean(dim=-1, keepdim=True)
    var = xf.var(dim=-1, keepdim=True, unbiased=False)
    norm = (xf - mean) / torch.sqrt(var + self.eps)
    return (norm.to(dtype) * self.weight + self.bias)
```
This is the standard from-scratch fp16-safe LayerNorm pattern (nanoGPT uses `F.layer_norm`, which
does the same internally). Verify the existing fp32 oracle test still passes.

### WR-02: `sdpa` attention branch ignores `config.dropout`; manual branch applies it — asymmetric behavior

**File:** `src/personacore/model/gpt.py:96-104`
**Issue:** The manual branch applies `self.attn_dropout` to the attention weights (line 103), but
the `sdpa` branch hardcodes `dropout_p=0.0` (line 97), ignoring `config.dropout` entirely. With
the locked `dropout=0.0` default this is currently inert, but (a) it is a latent bug — if dropout
is ever enabled for the real pretrain, the two `attn_impl` paths regularize differently, and (b)
it quietly undermines the equivalence narrative: the paths are only guaranteed equivalent when
dropout is 0, yet nothing in the code enforces or documents that. The equivalence test happens to
pass only because the default is 0 and `eval()` disables dropout.
**Fix:** Honor the configured dropout in both branches and gate it on training mode, or store the
rate and pass it through:
```python
if self.attn_impl == "sdpa":
    y = F.scaled_dot_product_attention(
        q, k, v, is_causal=True,
        dropout_p=self.attn_dropout.p if self.training else 0.0,
    )
```
At minimum, document that `attn_impl="sdpa"` is only numerically equivalent to `"manual"` when
`dropout == 0.0`.

### WR-03: `attn_impl` is silently accepted for any string — unknown values fall through to the manual path

**File:** `src/personacore/model/gpt.py:96-98`
**Issue:** The branch is `if self.attn_impl == "sdpa": ... else: <manual>`. Any value that is not
exactly `"sdpa"` (e.g. a typo like `"manaul"`, `"flash"`, or `None`) silently runs the manual
path with no error. Because `attn_impl` is a free-form constructor string (not validated against
an enum or set), a caller mis-toggling the equivalence oracle would get the manual path and a
falsely-passing "equivalence" comparison. This is a quiet-failure mode in exactly the toggle the
phase relies on to prove correctness.
**Fix:** Validate in `CausalSelfAttention.__init__` (and/or `GPT.__init__`):
```python
if attn_impl not in ("manual", "sdpa"):
    raise ValueError(f"attn_impl must be 'manual' or 'sdpa', got {attn_impl!r}")
self.attn_impl = attn_impl
```

### WR-04: Manual attention softmax computed in fp16 under autocast — divergence from the sdpa oracle in the real training dtype

**File:** `src/personacore/model/gpt.py:99-104`
**Issue:** Under fp16 autocast, the `q @ k.T` scores, the `masked_fill(-inf)`, and `F.softmax`
all run in fp16 in the manual branch. `F.scaled_dot_product_attention` (the sdpa branch) upcasts
the softmax to fp32 internally on its math backend. So the equivalence the test proves at
`atol=1e-5` holds only in fp32 (the test runs on CPU with autocast disabled); during fp16 GPU
training the two paths are NOT bit-equivalent, and the manual path is the less numerically stable
one (fp16 softmax over `-inf`-masked rows can produce larger error and, in pathological score
ranges, `nan`). Since the manual path is the default training path, this is a real numerical-
robustness concern, not just a test artifact.
**Fix:** Compute the attention scores/softmax in fp32 in the manual branch, mirroring sdpa:
```python
att = (q @ k.transpose(-2, -1)) / math.sqrt(self.d_head)
att = att.masked_fill(self.tril[:, :, :T, :T] == 0, float("-inf"))
att = F.softmax(att.float(), dim=-1).to(q.dtype)
att = self.attn_dropout(att)
y = att @ v
```
This keeps the manual path numerically aligned with the oracle in the dtype it actually trains in.

## Info

### IN-01: Unused import in the attention-equivalence test

**File:** `tests/test_gpt_attention_equiv.py:15`
**Issue:** `from torch.nn.functional import scaled_dot_product_attention` is imported and silenced
with `# noqa: F401`, but never used in the test — the oracle is exercised inside `GPT(attn_impl="sdpa")`,
not directly. The import and its comment ("oracle the impl uses") are misleading dead code.
**Fix:** Remove the import and the `# noqa`; the comment can move into the module docstring if the
intent is to document which primitive the impl relies on.

### IN-02: Variable shadowing of `B, T` in `forward`

**File:** `src/personacore/model/gpt.py:189,201`
**Issue:** `B, T = idx.shape` (line 189) is re-unpacked as `B, T, V = logits.shape` (line 201).
The reuse is harmless (values are consistent) but mildly confusing; the second unpack only needs
`V`. Minor readability nit, retained verbatim from `bigram.py` for contract parity, so likely
intentional.
**Fix (optional):** `V = logits.size(-1)` instead of re-unpacking `B, T, V`.

### IN-03: `tril` mask uses float buffer + `== 0` comparison where a bool buffer is clearer and cheaper

**File:** `src/personacore/model/gpt.py:80-86,101`
**Issue:** The causal buffer is a float `tril(ones(...))` compared with `== 0` each forward. A
`bool` mask (`torch.tril(...).bool()`) makes intent explicit, avoids the per-step float-to-bool
comparison, and removes any ambiguity about the buffer participating in dtype/autocast casts. Not
a correctness issue (the comparison is exact for 0.0/1.0), purely clarity/hygiene.
**Fix:**
```python
self.register_buffer(
    "tril",
    torch.tril(torch.ones(config.block_size, config.block_size, dtype=torch.bool)).view(
        1, 1, config.block_size, config.block_size),
    persistent=False,
)
# in forward:
att = att.masked_fill(~self.tril[:, :, :T, :T], float("-inf"))
```

---

_Reviewed: 2026-06-05T16:13:23Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
