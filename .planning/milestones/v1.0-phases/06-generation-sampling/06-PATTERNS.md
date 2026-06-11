# Phase 6: Generation & Sampling - Pattern Map

**Mapped:** 2026-06-06
**Files analyzed:** 5 new (4 package modules + 1 test file)
**Analogs found:** 5 / 5

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/personacore/generation/__init__.py` | package barrel | n/a (re-export) | `src/personacore/training/__init__.py` | exact (sibling package barrel) |
| `src/personacore/generation/sampling.py` | utility (pure logits transforms) | transform | `src/personacore/training/loop.py::sample` (logits→probs idiom) + `src/personacore/training/schedule.py` (pure-function utility module) | role-match |
| `src/personacore/generation/core.py` | service (autoregressive decode loop) | streaming / event-driven (generator yields) | `src/personacore/training/loop.py::sample` (≈106-119) | exact (direct supersession, D-11) |
| `src/personacore/generation/text.py` | service (str→str wrapper) | streaming (running-buffer delta) | `src/personacore/training/loop.py` periodic sample hook + `src/personacore/tokenizer/bpe.py::encode/decode` | role-match |
| `tests/test_generation.py` | test | request-response (assert on returns) | `tests/test_gpt_model.py` + `tests/test_train_loop.py` (monkeypatch/spy) | exact (sibling unit test) |

All five files are **new**. No existing source file is modified — D-11 only requires `generate()` to *supersede* `training/loop.py::sample` in capability; the training loop and its `training/__init__` barrel (which still exports `sample`) stay untouched.

## Pattern Assignments

### `src/personacore/generation/core.py` (service, streaming generator)

**Analog:** `src/personacore/training/loop.py::sample` (lines 105-119) — the minimal sampler this supersedes.

**`@torch.no_grad()` decorator + last-position logits + multinomial idiom** (loop.py:105-119):
```python
@torch.no_grad()
def sample(model, idx, max_new_tokens, temperature=1.0):
    for _ in range(max_new_tokens):
        logits, _ = model(idx)  # (B, T, V)
        logits = logits[:, -1, :] / temperature
        probs = torch.softmax(logits, dim=-1)
        next_id = torch.multinomial(probs, num_samples=1)
        idx = torch.cat([idx, next_id], dim=1)
    return idx
```

**What `core.py` keeps identical:** the `@torch.no_grad()` decorator, the `for _ in range(max_new_tokens)` loop bound, the `logits, _ = model(idx_cond)` call against the **locked forward contract**, the `logits[:, -1, :]` last-position slice, `torch.softmax` → `torch.multinomial`, and `torch.cat([idx, next_id], dim=1)` append.

**What `core.py` adds over the analog** (per CONTEXT D-04/D-05 + RESEARCH Patterns 4-5):
- Context crop **before** each forward (mandatory — see forward assert below): `idx_cond = idx if idx.size(1) <= bs else idx[:, -bs:]` where `bs = model.config.block_size` (do NOT hardcode 256).
- Becomes a **generator** that `yield`s `int(next_id)` per step instead of returning a tensor (D-04).
- `return` (stop) the instant `next_id == eos_id`, **before** appending/yielding it (D-05).
- Delegates the logit→id decision to `sampling.next_token(...)` (greedy / temp / top-k / top-p).
- Threads a `generator=` (torch.Generator) into `torch.multinomial` for seeded determinism.
- Add a `collect(model, idx, **kw)` drain helper returning the full `(1, T)` LongTensor (D-02).

**Forward contract this MUST call (never bypass)** — `src/personacore/model/gpt.py:188-204`:
```python
def forward(self, idx, targets=None):
    B, T = idx.shape
    assert T <= self.config.block_size, f"seq len {T} > block_size {self.config.block_size}"
    ...
    logits = self.lm_head(x)  # (B, T, V)
    if targets is None:
        return logits, None
    ...
    return logits, loss
```
The `assert T <= self.config.block_size` (gpt.py:190) is what makes context cropping mandatory in the core loop. `self.config` is stored on the model, so `model.config.block_size` / `model.config.eos_id` are available — read defaults from there (RESEARCH Pattern 4/5, anti-pattern "magic 256").

---

### `src/personacore/generation/sampling.py` (utility, pure logits transforms)

**Analog:** the `logits[:, -1, :] / temperature` + `softmax` + `multinomial` block in `loop.py::sample` (above), factored into separately-testable pure functions; module-shape mirrors `src/personacore/training/schedule.py` (a small pure-function utility module imported by the loop).

**Functions to implement** (RESEARCH Patterns 2-3 — `apply_temperature`, `top_k_filter`, `top_p_filter`, `next_token`):
- `top_k_filter` — verbatim nanoGPT idiom (RESEARCH Pattern 3): `v, _ = torch.topk(logits, min(k, size)); logits[logits < v[:, [-1]]] = float("-inf")`. Defensive `.clone()` since these are standalone funcs (RESEARCH anti-pattern).
- `top_p_filter` — sort → cumsum-softmax → shift-right mask, always keep top-1 token (RESEARCH Pattern 3, Pitfall 5; flagged `[ASSUMED]` — pin with `test_top_p_nucleus_exact`).
- `next_token(logits_last, *, temperature, top_k, top_p, greedy, generator)` — composition order **temperature → top-k → top-p → softmax → multinomial(generator=g)**; greedy short-circuits to `torch.argmax(..., keepdim=True)` (no RNG).

**Why a separate module:** keeps `core.py` readable and makes the filters unit-testable in isolation (matches the per-concern split already used in `training/` — `data.py` / `loss.py` / `schedule.py` / `loop.py`).

---

### `src/personacore/generation/text.py` (service, str→str streaming wrapper)

**Analog A — the `[eos_id]`-seed + decode register** (`loop.py` periodic sample hook, ≈375-380, motivates D-03): the training sampler seeds with `[eos_id]` as a start-of-document marker and calls `tokenizer.decode`. The wrapper mirrors this: encode prompt as `[eos_id] + tokenizer.encode(prompt)`, empty prompt → just `[eos_id]` (D-03).

**Analog B — tokenizer encode/decode contract** (`src/personacore/tokenizer/bpe.py:151, 189-209`):
```python
def encode(self, text, allowed_special="all"): ...   # text -> list[int] ids
def decode(self, ids):                               # ids  -> str
    ...
    return b"".join(parts).decode("utf-8")           # errors="strict" — raises on partial bytes
```
**Load-bearing fact:** `decode` is **strict UTF-8** (bpe.py:196-209) — it `raise`s on a non-round-trippable byte stream rather than emitting U+FFFD. This is exactly why D-06's **running-buffer delta** decode is required: per-token `decode([tok])` would crash or split a multi-byte glyph; decoding the whole accumulated buffer each step and yielding only the new string suffix guarantees complete characters (RESEARCH Pattern 6, Pitfall 3).

**Tokenizer is loaded via the package barrel** — `from personacore.tokenizer import from_json` (see `src/personacore/tokenizer/__init__.py`), using the frozen `artifacts/tokenizer.json` unchanged (never retrain).

**Wrapper shape** (D-01/D-02/D-06): generator of new-suffix strings; thin `"".join(...)` convenience for non-streaming callers; strips the prompt and returns only the continuation.

---

### `tests/test_generation.py` (test, CPU-only)

**Analog A — tiny-model construct-and-assert idiom** (`tests/test_gpt_model.py`):
```python
import torch
from personacore.config import ModelConfig
from personacore.model import GPT

def test_forward_contract():
    model = GPT(ModelConfig(block_size=16))
    idx = torch.randint(0, 8192, (2, 8))
    logits, loss = model(idx)
    assert logits.shape == (2, 8, 8192)
```
Plus the seed-first determinism idiom (`test_gpt_model.py:39` `torch.manual_seed(1337)`). Build GEN-03 tests on a tiny CPU `GPT(ModelConfig(block_size=8, vocab_size=16, n_layer=1, n_head=1, n_embd=8, eos_id=...))` fixture — never `best.pt` (RESEARCH Wave-0 Gaps).

**Analog B — monkeypatch/spy for controlled logits** (`tests/test_train_loop.py:42-58`): the spy-scaler + `monkeypatch.setattr` pattern is the model to follow for forcing `eos_id` as the argmax at a known step (EOS-stop test) or pinning the nucleus token set (top-p exactness). Module docstring should state the "RED until implemented, CPU-only, GPU-free" posture every test file here uses.

**Determinism mechanism (GEN-03):** greedy uses `argmax` (no Generator); sampled uses two `torch.Generator().manual_seed(0)` instances passed into separate `collect(..., generator=gN)` calls — assert equal. Prefer this over global `torch.manual_seed` (RESEARCH Pitfall 2; the global-RNG anti-pattern). Note: `conftest.py` currently only holds `simulate_pascal`; add any new shared fixture either inline or there.

**Tests to cover** (RESEARCH Phase Requirements → Test Map): `test_output_shape`, `test_greedy_deterministic`, `test_seeded_sampling_deterministic`, `test_eos_stop`, `test_past_block_size_no_crash`, `test_top_k_top_p_support`, `test_temperature`, `test_top_p_nucleus_exact`.

---

## Shared Patterns

### Package barrel / `__init__.py` export convention
**Source:** `src/personacore/training/__init__.py` (and identical shape in `model/__init__.py`, `tokenizer/__init__.py`)
**Apply to:** `generation/__init__.py`
```python
"""<one-line package purpose> (D-09) — public import surface."""

from .core import collect, generate
from .sampling import top_k_filter, top_p_filter   # (export the public surface)
from .text import generate_text                     # str->str wrapper

__all__ = ["generate", "collect", "generate_text", ...]
```
Every package barrel is a thin re-export with a module docstring ending in the relevant decision tag, an explicit `__all__`, and `from .module import name` lines — so callers write `from personacore.generation import generate` instead of reaching into submodules.

### `@torch.no_grad()` + `model.eval()` inference posture
**Source:** `loop.py:70` (`estimate_loss`) and `loop.py:105` (`sample`) both decorate with `@torch.no_grad()`; `estimate_loss` calls `model.eval()` then restores `model.train()`.
**Apply to:** `core.py` (decorate the generator) and `text.py` / a load helper (call `model.eval()` once before generation). `dropout=0.0` in `ModelConfig` (config.py:92) makes train/eval equivalent, but `eval()` is the correct posture.

### Locked `forward(idx, targets=None) -> (logits, loss)` contract
**Source:** `src/personacore/model/gpt.py:188-204`
**Apply to:** `core.py` — always `logits, _ = model(idx_cond)` and read `logits[:, -1, :]`. Never add a `generate`/`sample` method to `GPT` (RESEARCH anti-pattern — the class deliberately ships none, preserving the LoRA/EWC seam).

### Config as single source for sizes
**Source:** `src/personacore/config.py` — `ModelConfig.block_size=256` (c.87/88), `vocab_size=8192`, `eos_id=8184`; `RuntimeConfig` device CUDA→MPS→CPU.
**Apply to:** `core.py` (`block_size`/`eos_id` default from `model.config.*`, not literals) and any load helper (device from `RuntimeConfig`). Generation must run on CPU and MPS; tests are CPU-only.

### Strict-decode → running-buffer streaming
**Source:** `src/personacore/tokenizer/bpe.py:196-209` (strict UTF-8 decode, raises on partial bytes)
**Apply to:** `text.py` only — decode the cumulative buffer each step and diff the string suffix (D-06). This is the single reason per-token decode is forbidden in the wrapper.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `top_p_filter` (within `sampling.py`) | utility | transform | No nucleus-sampling code exists in-repo; the sort-cumsum-shift mask is `[ASSUMED]` standard idiom (RESEARCH Pattern 3 / A1). Pin behavior with `test_top_p_nucleus_exact` rather than copy from an analog. |

(No whole *file* lacks an analog; only this one filter has no in-repo precedent. The closest in-repo precedent for `top_k_filter` is the nanoGPT-verbatim idiom already cited in RESEARCH Pattern 3.)

## Metadata

**Analog search scope:** `src/personacore/` (all packages), `tests/`
**Files scanned:** 20 source modules + 33 test files (listed); read in full or targeted: `training/loop.py` (1-130), `model/gpt.py` (160-205), `tokenizer/bpe.py` (151-210), `tokenizer/io.py`/`config.py` (grep), the three package `__init__.py` barrels, `tests/test_gpt_model.py`, `tests/conftest.py`, `tests/test_train_loop.py` (1-60)
**Pattern extraction date:** 2026-06-06
