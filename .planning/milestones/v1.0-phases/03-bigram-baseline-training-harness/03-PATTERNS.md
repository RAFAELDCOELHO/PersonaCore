# Phase 3: Bigram Baseline & Training Harness - Pattern Map

**Mapped:** 2026-06-04
**Files analyzed:** 14 (6 source/script + 7 tests + 1 fixture)
**Analogs found:** 14 / 14 (every new file has a same-repo analog — Phase 3 is greenfield modules that DRIVE existing Phase-1/2 primitives)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/personacore/model/__init__.py` | package-init | — | `src/personacore/tokenizer/__init__.py` | exact (public-surface barrel) |
| `src/personacore/model/bigram.py` | model | transform (idx→logits→loss) | `src/personacore/tokenizer/bpe.py` (nn-free) + nanoGPT bigram (RESEARCH §Pattern 1) | role-match (new `nn.Module`; no existing model) |
| `src/personacore/training/__init__.py` | package-init | — | `src/personacore/tokenizer/__init__.py` | exact |
| `src/personacore/training/loss.py` | utility | transform | `src/personacore/seeding.py` (thin pure-fn module) | role-match |
| `src/personacore/training/schedule.py` | utility/factory | transform | `src/personacore/config.py` `autocast()` factory + `checkpoint.py` (scheduler contract) | role-match |
| `src/personacore/training/data.py` | data-loader | file-I/O + batch | `scripts/train_tokenizer.py` (fixture load + `from_json`) + RESEARCH §Code Examples | role-match |
| `src/personacore/training/loop.py` | service/orchestrator | event-driven (step loop) | `tests/test_checkpoint.py::_train_step` (loop skeleton) + `checkpoint.py`/`logging.py` callers | role-match |
| `scripts/train_bigram.py` | entry-point | request-response | `scripts/train_tokenizer.py` + `scripts/preflight_demo.py` | exact |
| `tests/test_bigram_model.py` | test | unit | `tests/test_tokenizer_roundtrip.py` | role-match (shape/contract asserts) |
| `tests/test_assemble_loss.py` | test | unit | `tests/test_config.py` (pure-fn behavior asserts) | role-match |
| `tests/test_lr_schedule.py` | test | unit | `tests/test_checkpoint.py` (state_dict round-trip) | role-match |
| `tests/test_data_split.py` | test | unit | `tests/test_tokenizer_io.py` (fixture-path + `from_json`) | role-match |
| `tests/test_train_loop.py` | test | unit | `tests/test_checkpoint.py::_train_step` + `simulate_pascal` conftest pattern | role-match |
| `tests/test_overfit_batch.py` | test | unit | `tests/test_checkpoint.py` (seeded deterministic loop) | role-match |
| `tests/test_resume_curve.py` | test | unit | `tests/test_checkpoint.py::test_resume_identical_trajectory` (CALLED OUT analog) + `test_logging.py` | exact |
| `tests/fixtures/bigram_corpus.txt` | fixture | data | `tests/fixtures/tiny_corpus.txt` | exact |

---

## Pattern Assignments

### `src/personacore/model/__init__.py` (package-init)

**Analog:** `src/personacore/tokenizer/__init__.py` (lines 1-17)

**Pattern — thin public-surface barrel with module docstring + `__all__`:**
```python
"""From-scratch GPT-shaped models (D-09) — public import surface."""

from .bigram import BigramLanguageModel

__all__ = [
    "BigramLanguageModel",
]
```
Copy the one-line module docstring + relative import + explicit `__all__` shape exactly. Phase 4 adds `from .gpt import GPT` here beside the bigram (D-09).

---

### `src/personacore/model/bigram.py` (model, transform)

**Analog:** RESEARCH.md §Pattern 1 (the locked contract) for the body; `src/personacore/tokenizer/bpe.py` for the repo's module-docstring + imperative-docstring style.

**Module docstring style to match** (every repo module opens with a `"""..."""` naming its decision ID — see `config.py:1-13`, `checkpoint.py:1-21`, `seeding.py:1-15`):
```python
"""Lookup-table bigram LM (MODEL-01) — de-risks the harness, never pretrained (D-01).

Implements the LOCKED model<->harness contract (D-02): ``forward(idx, targets=None) ->
(logits, loss)`` returns base cross-entropy ONLY (D-03 — loss assembly lives in the loop,
not the model). Phase 4's GPT replaces __init__ + the pre-CE body and reuses this signature
and the (B*T, V) flatten (D-02a) UNCHANGED.
"""
```

**Core pattern — LOCKED `forward` contract** (RESEARCH §Pattern 1, lines 194-206):
```python
import torch.nn as nn
import torch.nn.functional as F


class BigramLanguageModel(nn.Module):
    def __init__(self, vocab_size: int):
        super().__init__()
        self.token_table = nn.Embedding(vocab_size, vocab_size)  # (V, V) lookup

    def forward(self, idx, targets=None):              # LOCKED signature (D-02)
        logits = self.token_table(idx)                 # (B, T, V)
        if targets is None:
            return logits, None
        B, T, V = logits.shape
        loss = F.cross_entropy(logits.view(B * T, V), targets.view(B * T))  # D-02a
        return logits, loss                            # base CE only — no penalties (D-03)
```

**Typing convention:** repo uses explicit param/return type hints on public signatures but keeps tensor args untyped (see `config.py:55` `def autocast(self):`, `bpe.py:151` `def encode(self, text, allowed_special="all"):`). `vocab_size: int` is annotated; `idx`/`targets` tensors are not — match that.

**Do NOT** put `assemble_loss` or any penalty here (RESEARCH Anti-Patterns) — the model stays pure (D-03).

---

### `src/personacore/training/__init__.py` (package-init)

**Analog:** `src/personacore/tokenizer/__init__.py`

```python
"""Training harness (D-09) — loop, loss assembly, LR schedule, data path."""

from .data import get_batch, load_split
from .loss import assemble_loss
from .schedule import build_lr_lambda, build_scheduler
from .loop import train

__all__ = ["assemble_loss", "build_lr_lambda", "build_scheduler", "get_batch", "load_split", "train"]
```
(Final export list is the planner's call; keep the barrel shape.)

---

### `src/personacore/training/loss.py` (utility, transform)

**Analog:** `src/personacore/seeding.py` (a thin pure-function module with a decision-anchored docstring).

**Core pattern** (RESEARCH §Code Examples, lines 387-392; D-04):
```python
"""Loop-level loss assembly — the M2 EWC seam (D-03/D-04, TRAIN-06).

``assemble_loss`` is the loop's extension point: M1 passes ``()`` -> returns base_loss
UNCHANGED (identity); M2 EWC will pass ``(fisher_penalty,)`` with ZERO changes here. Kept in
the loop (not the model, D-03) so the model stays pure. No callbacks/lazy callables (D-04).
"""


def assemble_loss(base_loss, extra_penalties=()):
    """base + sum(extra). Each penalty is a precomputed scalar tensor. () -> identity."""
    total = base_loss
    for p in extra_penalties:
        total = total + p
    return total
```

---

### `src/personacore/training/schedule.py` (utility/factory, transform)

**Analog:** `config.py:55-61` (`autocast()` returns a configured torch object — factory idiom) + the `checkpoint.py:55,87-88` scheduler `state_dict()`/`load_state_dict()` contract (D-05).

**Core pattern — hand-rolled warmup+cosine as a `LambdaLR`** (RESEARCH §Pattern 4, lines 251-262):
```python
"""Hand-rolled warmup + cosine LR as a resumable LambdaLR (D-08).

MUST be a ``torch.optim.lr_scheduler`` object, not a bare function: ``checkpoint.py`` calls
``scheduler.state_dict()`` (D-05), so resume restores ``last_epoch`` and continues the schedule
at the right step. The lambda math is written by hand (from-scratch ethos); LambdaLR only
serializes the step counter (A1 — verified by the resume test).
"""

import math

from torch.optim.lr_scheduler import LambdaLR


def build_lr_lambda(warmup_steps: int, max_steps: int, min_ratio: float = 0.1):
    def lr_lambda(step: int) -> float:               # MULTIPLIER on base lr
        if step < warmup_steps:
            return (step + 1) / max(1, warmup_steps)
        if step >= max_steps:
            return min_ratio
        progress = (step - warmup_steps) / max(1, max_steps - warmup_steps)
        cosine = 0.5 * (1.0 + math.cos(math.pi * progress))
        return min_ratio + (1.0 - min_ratio) * cosine
    return lr_lambda


def build_scheduler(optimizer, train_cfg):
    return LambdaLR(optimizer, build_lr_lambda(train_cfg.warmup_steps, train_cfg.max_steps))
```
`warmup_steps`/`max_steps` come from `TrainConfig` (`config.py:89-90`, defaults 5000/100). The harness MUST rebuild `build_scheduler(...)` identically before `load_checkpoint` so `last_epoch` restore is meaningful (A1).

---

### `src/personacore/training/data.py` (data-loader, file-I/O + batch)

**Analog:** `scripts/train_tokenizer.py:36-40` (fixture `read_text` + frozen-tokenizer load) and `tests/test_tokenizer_io.py:34` (`from_json`). Tokenizer loaded via `from_json` (NOT `.train()` — Pitfall 6).

**Import/load pattern — frozen tokenizer** (matches the repo's `from personacore.tokenizer import ...` surface, `__init__.py:1-17`):
```python
"""Committed-fixture data path (D-06): encode -> uint16 -> doc-level split -> get_batch.

Bounded fixture ONLY — the full-corpus uint16 memmap + TinyStories fetch is Phase 5 (PRE-01).
Doc-level split on eos_id=8184 (never mid-document) gives a provable no-leakage train/val
guarantee (TRAIN-03). nanoGPT get_batch draws random contiguous windows.
"""

import numpy as np

from personacore.tokenizer import from_json
```

**Doc-level split (no leakage)** (RESEARCH §Code Examples, lines 351-368; Pitfall 3 — split into TWO arrays on `eos_id`, never index a single flat array):
```python
def load_split(fixture_path, eos_id=8184, val_docs=1):
    tok = from_json("artifacts/tokenizer.json")          # FROZEN — never retrain (Pitfall 6)
    text = open(fixture_path, encoding="utf-8").read()
    ids = tok.encode(text, allowed_special="all")        # eos -> atomic 8184
    docs, cur = [], []
    for t in ids:
        cur.append(t)
        if t == eos_id:
            docs.append(cur); cur = []
    if cur:
        docs.append(cur)
    assert len(docs) >= 2, "fixture must contain >= 2 documents (D-06)"
    train_ids = np.array([t for d in docs[:-val_docs] for t in d], dtype=np.uint16)
    val_ids = np.array([t for d in docs[-val_docs:] for t in d], dtype=np.uint16)
    return train_ids, val_ids
```

**`get_batch` window sampler** (RESEARCH §Code Examples, lines 376-380; bound `i` to `len(arr)-block_size-1` so windows never overrun — Pitfall 3; cast `uint16`→`int64` for `nn.Embedding`):
```python
def get_batch(arr, batch_size, block_size, device):
    ix = np.random.randint(0, len(arr) - block_size - 1, size=batch_size)
    x = torch.stack([torch.from_numpy(arr[i:i + block_size].astype(np.int64)) for i in ix])
    y = torch.stack([torch.from_numpy(arr[i + 1:i + 1 + block_size].astype(np.int64)) for i in ix])
    return x.to(device), y.to(device)
```

---

### `src/personacore/training/loop.py` (service/orchestrator, event-driven)

**Analog:** `tests/test_checkpoint.py:27-40` (`_train_step` skeleton: `zero_grad → backward → optimizer.step() → scheduler.step()`) extended with the AMP/accum ordering; calls existing `RuntimeConfig.autocast()`, `save_checkpoint`, `CSVLogger`, `assemble_loss`.

**AMP step ordering with grad accumulation — the critical seam** (RESEARCH §Pattern 2, lines 215-227; ordering is load-bearing, see Anti-Patterns):
```python
optimizer.zero_grad(set_to_none=True)
for micro in range(grad_accum_steps):
    xb, yb = get_batch(train_ids, cfg.batch_size, model_cfg.block_size, runtime.device)
    with runtime.autocast():                      # RuntimeConfig.autocast() — single AMP source
        logits, base_loss = model(xb, yb)
        total = assemble_loss(base_loss, ())      # identity in M1 (D-04)
        loss = total / grad_accum_steps
    scaler.scale(loss).backward()
scaler.unscale_(optimizer)                        # UNSCALE before clip (mandatory order)
torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.grad_clip)
scaler.step(optimizer)
scaler.update()
scheduler.step()                                  # ONCE per optimizer step, NOT per micro-batch
```

**GradScaler tied to the config's AMP flag** (RESEARCH §Pattern 3, lines 239-240; the loop must NOT call `torch.cuda.*` — `RuntimeConfig` already auto-disables AMP on CPU and guards bf16-on-Pascal, `config.py:44-53`):
```python
from torch.amp import GradScaler

scaler = GradScaler(device=runtime.device.split(":")[0], enabled=runtime.amp)
```

**Periodic validation** (RESEARCH §Code Examples, lines 399-408; `@torch.no_grad()` + `model.eval()`/`model.train()` toggle):
```python
@torch.no_grad()
def estimate_loss(model, val_ids, cfg, model_cfg, device, iters=20):
    model.eval()
    losses = [model(*get_batch(val_ids, cfg.batch_size, model_cfg.block_size, device))[1].item()
              for _ in range(iters)]
    model.train()
    return sum(losses) / len(losses)
```

**Optimizer + logging wiring** (use `torch.optim.AdamW` with `TrainConfig.lr`/`weight_decay`; reuse `CSVLogger` unchanged, `logging.py:24-38`; reuse `save_checkpoint(...)` unchanged, `checkpoint.py:32-70`):
```python
optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
csv = CSVLogger(log_path, fieldnames=["step", "train_loss", "val_loss", "lr", "tokens", "wall_clock"])
# ... each eval interval:
csv.log(step=step, train_loss=..., val_loss=..., lr=scheduler.get_last_lr()[0], tokens=..., wall_clock=...)
save_checkpoint(ckpt_path, model=model, optimizer=optimizer, scheduler=scheduler,
                step=step, model_config=model_cfg, train_config=cfg, git_sha=git_sha())
```

**Resume discipline** (RESEARCH Anti-Patterns + Pitfall 4): on resume, call `load_checkpoint(...)` and read `step` from the returned dict (`checkpoint.py:97`); do NOT call `seed_everything` again; re-open the SAME CSV path so `CSVLogger` appends without a duplicate header.

**Minimal sampling** (D-11, Open Question 2 — put a tiny free function HERE, not in the model, so Phase-6's `generate()` supersedes it without a model rewrite):
```python
@torch.no_grad()
def sample(model, idx, max_new_tokens, temperature=1.0):
    for _ in range(max_new_tokens):
        logits, _ = model(idx)                    # (B, T, V)
        logits = logits[:, -1, :] / temperature
        probs = torch.softmax(logits, dim=-1)
        idx = torch.cat([idx, torch.multinomial(probs, num_samples=1)], dim=1)
    return idx
```

---

### `scripts/train_bigram.py` (entry-point, request-response)

**Analog:** `scripts/train_tokenizer.py` (lines 30-49) and `scripts/preflight_demo.py` (lines 27-36). NO argparse (D-04) — module-constant paths + `main()` + `if __name__ == "__main__"`.

**Pattern to copy** (`train_tokenizer.py:25-49` — `_REPO_ROOT` path constants, `seed_everything` first, logic delegated to the package, single `print` summary):
```python
"""Thin entry: build configs -> seed -> train the bigram harness end-to-end (D-09).

Logic lives in src/personacore/{model,training}; this only wires configs + paths (mirrors
train_tokenizer.py / preflight_demo.py). NO argparse (D-04) — paths/hyperparams are constants/kwargs.
"""

import pathlib

from personacore.config import ModelConfig, RuntimeConfig, TrainConfig
from personacore.model import BigramLanguageModel
from personacore.seeding import seed_everything
from personacore.training import train

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
FIXTURE_PATH = _REPO_ROOT / "tests" / "fixtures" / "bigram_corpus.txt"


def main() -> None:
    seed_everything(TrainConfig().seed)            # FRESH run only (resume restores state)
    ...
    print(f"[train_bigram] done ...")


if __name__ == "__main__":
    main()
```

---

### `tests/test_bigram_model.py` (test, unit)

**Analog:** `tests/test_tokenizer_roundtrip.py` (module docstring + shape/contract asserts). Covers MODEL-01.

**Pattern:** import the unit under test, assert the `forward` contract — `forward(idx, None) -> (logits, None)`; `forward(idx, targets) -> (logits, loss)`; `logits.shape == (B, T, V)`; CE flatten correctness. CPU-only, no fixtures needed (random `idx` via seeded torch).
```python
import torch
from personacore.model import BigramLanguageModel

def test_forward_returns_logits_none_without_targets():
    model = BigramLanguageModel(vocab_size=32)
    idx = torch.randint(0, 32, (2, 5))
    logits, loss = model(idx)
    assert logits.shape == (2, 5, 32)
    assert loss is None
```

---

### `tests/test_assemble_loss.py` (test, unit)

**Analog:** `tests/test_config.py` (pure-function behavior asserts). Covers TRAIN-06 / D-04a.

**Pattern — identity-on-empty + additive** (D-04a):
```python
import torch
from personacore.training.loss import assemble_loss

def test_empty_is_identity():
    x = torch.tensor(2.5)
    assert torch.equal(assemble_loss(x, ()), x)

def test_additive_with_penalty():
    x, p = torch.tensor(2.0), torch.tensor(0.5)
    assert torch.equal(assemble_loss(x, (p,)), torch.tensor(2.5))
```

---

### `tests/test_lr_schedule.py` (test, unit)

**Analog:** `tests/test_checkpoint.py` (the `state_dict()`/`load_state_dict` round-trip idiom). Covers TRAIN-01 schedule.

**Pattern:** build optimizer + `build_scheduler`; assert warmup ramps 0→base over `warmup_steps`, cosine decays toward the floor, `last_epoch`/LR matches the lambda at step N (NOT N×accum — Pitfall 2), and `state_dict()` round-trips. Use a tiny `nn.Linear` + `AdamW` like `test_checkpoint.py:_build` (lines 19-24).

---

### `tests/test_data_split.py` (test, unit)

**Analog:** `tests/test_tokenizer_io.py` (fixture-path constant + `from_json` + behavior asserts, lines 17-54). Covers TRAIN-03.

**Pattern:** `CORPUS_PATH = pathlib.Path(__file__).parent / "fixtures" / "bigram_corpus.txt"` (mirror `test_tokenizer_io.py:19`); assert `load_split` returns disjoint train/val docs (NO leakage — Pitfall 3), `get_batch` shapes `(batch, block)`, dtype `int64`, indices in-bounds, and that `8184` appears at doc boundaries (Pitfall 6).

---

### `tests/test_train_loop.py` (test, unit)

**Analog:** `tests/test_checkpoint.py::_train_step` (lines 27-40) for the loop skeleton; `tests/conftest.py::simulate_pascal` (lines 6-16) for the device-monkeypatch idiom; inline `@pytest.mark.skipif(not torch.cuda.is_available())` for the GPU smoke test. Covers TRAIN-01/02.

**Patterns:**
- **AMP ordering (CPU, D-07a):** record the op sequence (spy on a wrapped scaler/optimizer or a call-log) and assert `unscale_` precedes `clip` precedes `step` precedes `update`, with one `unscale_` per optimizer step (Pitfall 1). A "did it run / loss decreased" test is INSUFFICIENT.
- **Grad-accum equivalence:** N micro-batches == 1 big batch within tolerance.
- **GPU fp16 smoke (D-07b):** `@pytest.mark.skipif(not torch.cuda.is_available())` — no `cuda` marker is registered in `pyproject.toml`, so use the inline `skipif` (Wave-0 note in RESEARCH §Validation).

---

### `tests/test_overfit_batch.py` (test, unit)

**Analog:** `tests/test_checkpoint.py` (seeded deterministic loop via `seed_everything`). Covers TRAIN-05 / D-10.

**Pattern:** `seed_everything(seed)` for determinism (Pitfall 5); a DEDICATED small `TrainConfig` (`warmup_steps=0`, ~200-500 `max_steps`, higher `lr` ~1e-2..1e-1 — Pitfall 5, Open Question 3); reuse ONE fixed batch every step; assert final loss below a small threshold (well under `ln(8192)≈9.0`; executor pins the exact threshold per A2).

---

### `tests/test_resume_curve.py` (test, unit) — PRIMARY resume analog

**Analog:** `tests/test_checkpoint.py::test_resume_identical_trajectory` (lines 43-80) — the CALLED-OUT analog. Extend its exact shape (reference run vs. kill+resume) to the bigram + real `LambdaLR` + the CSV log. Also reuse `tests/test_logging.py` (lines 32-50) for the CSV-restart assertion. Covers TRAIN-04/06.

**Pattern to copy** (`test_checkpoint.py:43-80`): run a reference of N+1 steps; run a second `seed_everything`-seeded run of N steps, `save_checkpoint`, build FRESH model/opt/sched, `load_checkpoint`, assert `ckpt["step"] == N`, take +1 step, assert next-step loss AND a sampled param match within `1e-6`. Extension: also concatenate pre-kill + post-resume CSV rows and assert they equal an uninterrupted run's rows (`test_logging.py:_read_rows` helper, lines 12-14), and assert the header appears exactly once across the restart (Pitfall 4).

```python
# Skeleton straight from test_checkpoint.py:43-80, retargeted to BigramLanguageModel + build_scheduler:
seed_everything(1234)
ref_model, ref_opt, ref_sched = _build_bigram()          # bigram + AdamW + build_scheduler
# ... N+1 reference steps, capture ref_next_loss + ref_param ...
seed_everything(1234)
# ... N steps, save_checkpoint, fresh objects, load_checkpoint, +1 step ...
assert abs(resumed_next_loss - ref_next_loss) < 1e-6
assert torch.allclose(resumed_param, ref_param, atol=1e-6)
```

---

### `tests/fixtures/bigram_corpus.txt` (fixture, data)

**Analog:** `tests/fixtures/tiny_corpus.txt` (TinyStories-style short sentences, plain UTF-8).

**Pattern:** ≥2 TinyStories-style documents separated by the literal `<|endoftext|>` (D-06) so the doc-level split has ≥1 whole doc in val. Match the lexical style of `tiny_corpus.txt` ("In the blue lake there lived a red owl. ...") so the frozen 8192-vocab tokenizer encodes it cleanly. Encoded array must contain `8184` at every document boundary (Pitfall 6).

---

## Shared Patterns

### Module docstring + decision-ID anchoring
**Source:** `config.py:1-13`, `checkpoint.py:1-21`, `seeding.py:1-15`, `logging.py:1-10`
**Apply to:** Every new source module
Every repo module opens with a `"""..."""` that names the requirement/decision ID it satisfies (e.g. `(D-04)`, `(TRAIN-06)`, `(MODEL-01)`) and states the load-bearing property. Match this — it is the single most consistent convention in the codebase.

### No CLI / thin scripts (Phase-1 D-04)
**Source:** `scripts/train_tokenizer.py`, `scripts/preflight_demo.py`
**Apply to:** `scripts/train_bigram.py`
NO argparse. Module-constant paths (`_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent`), `seed_everything` first, ALL logic delegated to `src/personacore/*`, one `print` summary, `main()` + `if __name__ == "__main__": main()`.

### RuntimeConfig is the single source of device/AMP truth
**Source:** `config.py:44-61` (`__post_init__` disables AMP on CPU + bf16-on-Pascal guard; `autocast()`)
**Apply to:** `training/loop.py`, `tests/test_train_loop.py`
The loop calls `runtime.autocast()` and reads `runtime.amp`/`runtime.device`. It MUST NOT call `torch.cuda.is_available()` or re-derive AMP/bf16 logic (RESEARCH Anti-Patterns). `GradScaler(device=runtime.device.split(":")[0], enabled=runtime.amp)`.

### Reuse checkpoint/logging/seeding UNCHANGED
**Source:** `checkpoint.py:32-97`, `logging.py:24-49`, `seeding.py:24-44`
**Apply to:** `training/loop.py`, `tests/test_resume_curve.py`
`save_checkpoint`/`load_checkpoint` (open-dict, RNG-state restore — D-05), `CSVLogger` (append-only, header-once), `seed_everything` (FRESH-run only — never on resume). The scheduler MUST be a `LambdaLR` object because `save_checkpoint` calls `scheduler.state_dict()` (`checkpoint.py:55`).

### Frozen tokenizer — load, never retrain
**Source:** `tokenizer/__init__.py:6` (`from_json`), `scripts/train_tokenizer.py` (the ONE place `.train()` is allowed), `bpe.py:151` (`encode(..., allowed_special="all")`)
**Apply to:** `training/data.py`, `tests/test_data_split.py`
Load via `from_json("artifacts/tokenizer.json")`; encode the fixture with `allowed_special="all"` so `<|endoftext|>` maps atomically to `eos_id=8184`. NEVER call `BPETokenizer().train()` in the harness (Pitfall 6).

### CPU-only, deterministic tests
**Source:** entire `tests/` suite; `conftest.py::simulate_pascal` for GPU simulation
**Apply to:** every Phase-3 test
All tests run GPU-free. Use `seed_everything` for determinism; `tmp_path` for checkpoint/CSV outputs; the only GPU-touching test (AMP fp16 smoke) guards with inline `@pytest.mark.skipif(not torch.cuda.is_available())` (no `cuda` marker registered in `pyproject.toml`).

## No Analog Found

No source file is left without a same-repo analog. Two items are "role-match via external reference" rather than an exact repo copy:

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `src/personacore/model/bigram.py` | model | transform | No existing `nn.Module` in the repo — the `forward` body comes from RESEARCH §Pattern 1 (nanoGPT-canonical). Repo analog supplies only the docstring/typing/style conventions, not the model code. |
| `src/personacore/training/loop.py` (AMP ordering) | orchestrator | event-driven | No existing AMP+grad-accum loop in the repo — the ordering comes from RESEARCH §Pattern 2 (PyTorch AMP docs). `test_checkpoint.py::_train_step` supplies only the bare step skeleton. |

## Metadata

**Analog search scope:** `src/personacore/`, `src/personacore/tokenizer/`, `scripts/`, `tests/`, `tests/fixtures/`, `artifacts/`
**Files scanned:** 17 source/test files read in full or in targeted ranges (`config.py`, `checkpoint.py`, `logging.py`, `seeding.py`, `tokenizer/__init__.py`, `tokenizer/bpe.py` encode, `scripts/preflight_demo.py`, `scripts/train_tokenizer.py`, `tests/test_checkpoint.py`, `tests/conftest.py`, `tests/test_logging.py`, `tests/test_tokenizer_io.py`, fixtures)
**Pattern extraction date:** 2026-06-04
