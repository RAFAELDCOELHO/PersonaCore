# Phase 5: TinyStories Pretraining - Pattern Map

**Mapped:** 2026-06-05
**Files analyzed:** 8 (2 new scripts, 2 modified src, 4 new tests)
**Analogs found:** 8 / 8 (every new/modified surface has a strong in-repo analog — Phase 5 is ~90% reuse)

> **Orientation for the planner:** Phase 5 builds almost no new infrastructure. The device layer
> (D-02: `preflight_device` + MPS-aware `RuntimeConfig`) is **already landed** — consume it, do not
> re-implement. Every new surface below mirrors an existing file line-for-line; the excerpts give
> the exact code to copy and the exact lines to change.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `scripts/encode_corpus.py` (NEW) | script (run-once data-prep) | batch / file-I/O | `scripts/train_bigram.py` + `scripts/preflight_demo.py` | role-match (thin no-CLI entry) |
| `scripts/pretrain_tinystories.py` (NEW, optional) | script (train entry) | request-response | `scripts/train_bigram.py` | exact (train entry idiom) |
| `src/personacore/training/data.py` (MODIFIED: +`get_batch_memmap`) | utility (data sampler) | streaming / file-I/O | `data.py::get_batch` (same file) | exact (swap in-RAM array → memmap) |
| `src/personacore/training/loop.py` (MODIFIED: +best-val, +periodic ckpt, +sample hook, +memmap branch) | service (train orchestration) | streaming / event-driven | `loop.py::train` / `estimate_loss` (same file) | exact (additive seams) |
| `tests/test_memmap_data.py` (NEW) | test | CRUD / file-I/O | `tests/test_data_split.py` | exact (data-path test idiom) |
| `tests/test_mps_smoke.py` (NEW) | test (skipif-guarded) | request-response | `tests/test_gpt_overfit.py` + `tests/test_preflight.py` | role-match (overfit gate + device skipif) |
| `tests/test_resume_memmap.py` (NEW) | test | event-driven | `tests/test_resume_curve.py` | exact (extends the resume test) |
| `tests/test_best_ckpt.py` (NEW) | test | CRUD | `tests/test_resume_curve.py` (curve-read helpers) + `checkpoint.py` save/load | role-match |

---

## Pattern Assignments

### `scripts/encode_corpus.py` (NEW — script, run-once file-I/O)

**Analog:** `scripts/train_bigram.py` (no-CLI thin entry, `_REPO_ROOT`-relative paths, frozen tokenizer load) + `scripts/preflight_demo.py` (path-constant convention).

**No-CLI thin-entry header + path constants** (copy from `train_bigram.py:14-27`):
```python
import pathlib

from personacore.tokenizer import from_json

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"
TRAIN_TXT = _REPO_ROOT / "data" / "TinyStoriesV2-GPT4-train.txt"
VAL_TXT   = _REPO_ROOT / "data" / "TinyStoriesV2-GPT4-valid.txt"
TRAIN_BIN = _REPO_ROOT / "data" / "train.bin"
VAL_BIN   = _REPO_ROOT / "data" / "val.bin"
EOS_ID = 8184  # ModelConfig.eos_id — do NOT inject extra EOS; source <|endoftext|> already separates docs
```

**Frozen-tokenizer load — NEVER `.train()`** (copy the exact comment + call from `data.py::load_split` line 32):
```python
tok = from_json(TOKENIZER_PATH)  # FROZEN production artifact — never retrain (Pitfall 6)
```
The tokenizer encode signature is `tok.encode(text, allowed_special="all")` (verified `tokenizer/bpe.py:151`) — `"all"` maps `<|endoftext|>` atomically to `8184`, exactly as `load_split` relies on it (`data.py:35`).

**Streaming encode → flat `uint16` `.bin`** (RESEARCH Pattern 1 — do NOT read 2.23 GB into one string; stream per-`<|endoftext|>` document, accumulate `uint16` shards, `np.concatenate`, `.tofile`). Mirror `load_split`'s `uint16` storage discipline (`data.py:53-54`):
```python
import numpy as np
# per-doc streaming → list of np.uint16 shards → np.concatenate → arr.tofile(bin_path)
# (nanoGPT .bin format; vocab 8192 < 65536 fits uint16)
```

**Post-build asserts** (the EOS / round-trip sanity from RESEARCH "Memmap Build Mechanics"):
```python
arr = np.fromfile(TRAIN_BIN, dtype=np.uint16)
assert np.count_nonzero(arr == EOS_ID) >= 1   # ≈ document count; no doubled/missing EOS
# round-trip: tok.decode(arr[:200].tolist()) reads as a coherent story prefix
```

**Print-summary close** (mirror `train_bigram.py:65-68` and `preflight_demo.py:30-33` — a `print(...)` summary, `if __name__ == "__main__": main()`).

---

### `scripts/pretrain_tinystories.py` (NEW, optional — train entry, request-response)

**Analog:** `scripts/train_bigram.py` (the canonical train-entry idiom — seed → configs → `train(...)` → sample → decode → print).

**Build-configs → seed → train** (copy structure from `train_bigram.py:30-50`):
```python
seed_everything(TrainConfig().seed)  # FRESH run only — resume restores RNG state instead.
runtime = RuntimeConfig()            # already MPS-aware (D-02 landed); resolves device="mps" on M3
model_cfg = ModelConfig()            # 6L/6H/384d, block_size=256, vocab 8192, eos 8184 (LOCKED)
model = GPT(model_cfg)               # the real model now, NOT BigramLanguageModel
```

**Preflight the active device before the long run** (use `preflight_device(strict=True)` from `preflight.py:25` — the long-run gate; asserts MPS active, never raises on Apple Silicon). NOTE the RESEARCH residual gap: do **not** copy `preflight_demo.py`'s `DATA_DIR = /kaggle/input/...` Kaggle-mount constant — preflight the **local** `data/train.bin`/`val.bin` paths instead.

**Wire `train(...)` at the memmap data source** (new kwargs — see the loop changes below), pass `log_path` (CSV curve), `checkpoint_path` (latest.pt), `best_checkpoint_path` (best.pt). AMP auto-off on MPS via `RuntimeConfig` — no scaler path to add.

**Sample-and-decode payoff** (copy `train_bigram.py:52-67`): use the minimal `sample()` from `loop.py`, `tok.decode(...)`, print. The decodable-id filtering there is a fixture-only artifact; on the real corpus the gap closes, so a straight `tok.decode(out_ids)` is fine.

---

### `src/personacore/training/data.py` (MODIFIED — add `get_batch_memmap`)

**Analog:** `data.py::get_batch` (lines 58-70, same file) — the memmap variant is the **same indexing**, swapping the in-RAM `arr` for a freshly-opened `np.memmap`.

**Existing in-RAM sampler to mirror** (`data.py:58-70`):
```python
def get_batch(arr, batch_size, block_size, device):
    ix = np.random.randint(0, len(arr) - block_size - 1, size=batch_size)
    x = torch.stack([torch.from_numpy(arr[i : i + block_size].astype(np.int64)) for i in ix])
    y = torch.stack(
        [torch.from_numpy(arr[i + 1 : i + 1 + block_size].astype(np.int64)) for i in ix]
    )
    return x.to(device), y.to(device)
```

**New memmap variant** (RESEARCH Pattern 2 — identical bound `len-block-1`, identical `uint16→int64`-at-batch-time cast, identical `.to(device)`; the **only** change is re-opening the memmap **every call** to avoid the documented nanoGPT leak, Pitfall 1):
```python
def get_batch_memmap(bin_path, batch_size, block_size, device):
    # Re-open the memmap EACH call (nanoGPT leak-avoidance — a long-lived mmap grows RSS).
    data = np.memmap(bin_path, dtype=np.uint16, mode="r")
    ix = np.random.randint(0, len(data) - block_size - 1, size=batch_size)
    x = torch.stack([torch.from_numpy(data[i : i + block_size].astype(np.int64)) for i in ix])
    y = torch.stack(
        [torch.from_numpy(data[i + 1 : i + 1 + block_size].astype(np.int64)) for i in ix]
    )
    return x.to(device), y.to(device)   # plain .to() — pin_memory/non_blocking are CUDA-only
```
Add `get_batch_memmap` to the `from .data import ...` re-export in `training/__init__.py:9` and `__all__` (mirror how `get_batch` is exported there).

---

### `src/personacore/training/loop.py` (MODIFIED — 4 minimal additive seams)

**Analog:** `loop.py::train` + `loop.py::estimate_loss` + `loop.py::sample` (same file) + `checkpoint.py::save_checkpoint` (reused saver). All four additions are **additive** — they must NOT touch the load-bearing AMP/accum/clip ordering in `_optimizer_step` (lines 101-126) or the resume RNG-restore contract (lines 233-239).

**Seam 1 — memmap data branch.** The data source already has a 3-mode branch (`loop.py:197-231`: `fixed_batch` / `corpus_path` / synthetic). Add a 4th mode pointing `batch_fn` at `get_batch_memmap`. Mirror the existing `corpus_path` branch (`loop.py:212-218`):
```python
# existing corpus_path branch to mirror:
elif corpus_path is not None:
    train_ids, val_ids = load_split(corpus_path, eos_id=eos_id)
    def batch_fn(_micro):
        return get_batch(train_ids, train_config.batch_size, model_cfg.block_size, runtime.device)
```
New memmap branch (a `train_bin`/`val_bin` kwarg pair, or branch on a `.bin` extension): `batch_fn` calls `get_batch_memmap(train_bin, ...)`, and `val_ids` carries the **val.bin path** (not an array).

**Seam 2 — `estimate_loss` accepts a memmap path.** Current signature (`loop.py:60-81`) takes an in-RAM `val_ids` array and calls `get_batch(val_ids, ...)`. The memmap path needs it to accept a path and call `get_batch_memmap`. Keep the **RNG snapshot/restore** wrapper intact (`loop.py:68, 80` — `rng = _rng_state()` … `_restore_rng(rng)`) — that is the resume-equality contract; only the inner sampler call changes:
```python
@torch.no_grad()
def estimate_loss(model, val_ids, train_cfg, model_cfg, device, iters=20):
    rng = _rng_state()                  # KEEP — never perturb the train trajectory
    model.eval()
    ...
    xb, yb = get_batch(val_ids, ...)    # ← branch to get_batch_memmap when val_ids is a path
    ...
    model.train()
    _restore_rng(rng)                   # KEEP
```

**Seam 3 — best-val-loss tracking (D-08).** Inside the existing eval branch (`loop.py:259-278`, where `val_loss` is already computed), add a running-minimum compare + a `best.pt` save. Reuse `save_checkpoint` verbatim from the end-of-call block (`loop.py:283-295`) — it already serializes a `val_loss=` field (`checkpoint.py:64`):
```python
# init before the loop:  best_val_loss = float("inf")
# inside the eval branch, after val_loss is computed:
if best_checkpoint_path is not None and val_loss < best_val_loss:
    best_val_loss = val_loss
    save_checkpoint(best_checkpoint_path, model=model, optimizer=optimizer,
                    scheduler=scheduler, scaler=scaler, step=step,
                    model_config=model_cfg, train_config=train_config,
                    git_sha=git_sha(), val_loss=val_loss)
```

**Seam 4 — periodic in-loop `latest.pt` + periodic sample hook.** RESEARCH Pitfall 5 / Open Q3: the current loop saves `latest.pt` **only** at end-of-call (`loop.py:283-295`). For kill-survivability add a periodic `save_checkpoint(checkpoint_path, ...)` every `K` steps **inside** the `while` loop (same call, just also fired on `step % K == 0`). For D-06 coherence checks, every `S` steps call the existing minimal `sample()` (`loop.py:84-98`) and `print(tok.decode(...))`:
```python
# every sample_interval steps (qualitative coherence check, D-06):
out = sample(model, seed_idx, max_new_tokens=...)[0].tolist()
print(tok.decode(out))     # NO Phase-6 generate() — minimal sample() only
```

> **Do NOT** introduce a GradScaler/fp16 path: `RuntimeConfig.__post_init__` (`config.py:55-59`) already forces `amp=False` on MPS; the loop's `scaler` is a disabled no-op there.

---

### `tests/test_memmap_data.py` (NEW — data-path unit tests, CPU-only)

**Analog:** `tests/test_data_split.py` — copy its structure verbatim: `pathlib` fixture path, frozen-tokenizer load, in-bounds/shape/dtype/shift asserts.

**Fixture + frozen-tokenizer header** (copy `test_data_split.py:13-27`):
```python
import pathlib
import torch
from personacore.tokenizer import from_json
from personacore.training.data import get_batch_memmap   # + the new fn

CORPUS_PATH = pathlib.Path(__file__).parent / "fixtures" / "tinystories_fixture.txt"  # NEW tiny multi-doc fixture
EOS_ID = 8184
```

**Shape/dtype/shift assert** (copy `test_data_split.py:57-65`, point at a `.bin` built in-test from the fixture):
```python
x, y = get_batch_memmap(bin_path, batch_size=4, block_size=16, device="cpu")
assert x.shape == (4, 16) and y.shape == (4, 16)
assert x.dtype == torch.int64 and y.dtype == torch.int64
```

**Tests to write** (per RESEARCH Validation Architecture): `test_encode_roundtrip` (decode(first N of train.bin) == `tok.encode(first raw doc)`), `test_one_eos_between_docs` (`count(==8184) ≈ num_docs`), `test_get_batch_memmap_inbounds` (max index < 8192, no overrun — copy `test_data_split.py:68-77`), `test_no_leakage_disjoint` (train.bin / val.bin from disjoint files — adapt the leakage idiom `test_data_split.py:44-54`).

**Shared fixture (Wave-0 gap):** add `tests/fixtures/tinystories_fixture.txt` — a few `<|endoftext|>`-separated micro-stories (mirror the existing `tests/fixtures/bigram_corpus.txt`).

---

### `tests/test_mps_smoke.py` (NEW — skipif-guarded smoke, D-01a)

**Analog:** `tests/test_gpt_overfit.py` (the overfit-one-batch gate) + `tests/test_preflight.py` (the `torch.backends.mps` device convention). This is the only non-CPU test; guard the WHOLE module.

**Skipif guard** (the device check pattern — `preflight.py:68` / `config.py:30` use `torch.backends.mps.is_available()`):
```python
import pytest
import torch

pytestmark = pytest.mark.skipif(
    not torch.backends.mps.is_available(), reason="MPS not available (CPU-only CI)"
)
```

**Overfit-one-batch on MPS** (copy `test_gpt_overfit.py:24-47` VERBATIM, changing ONLY `device="mps"` via `RuntimeConfig` and adding the finite-loss assert):
```python
seed_everything(1337)
model = GPT(ModelConfig())
fixed_idx     = torch.randint(0, 8192, (4, 16))
fixed_targets = torch.randint(0, 8192, (4, 16))
cfg = TrainConfig(lr=1e-3, warmup_steps=0, max_steps=300, batch_size=4)
final_loss = train(train_config=cfg, model=model,
                   fixed_batch=(fixed_idx, fixed_targets), return_final_loss=True)
assert torch.isfinite(torch.tensor(final_loss))   # finite-loss gate (D-01a)
assert float(final_loss) < math.log(8192) - 2.0   # overfit drives CE far below the uniform ceiling
```
`RuntimeConfig()` resolves to MPS automatically on the M3 — no manual `device=` plumbing (single-source-of-truth rule).

---

### `tests/test_resume_memmap.py` (NEW — resumability, CPU-only)

**Analog:** `tests/test_resume_curve.py` — extend `test_resume_identical_trajectory` (lines 38-79) to the memmap data source. Same kill+resume structure, same `seed_everything(1234)` → run-half → checkpoint → fresh-model → resume → assert trajectory equality within `1e-6`.

**Structure to copy** (`test_resume_curve.py:38-79`), swapping `corpus_path=CORPUS_PATH` for the memmap kwargs (`train_bin=`/`val_bin=` pointing at an in-test-built `.bin`):
```python
cfg = TrainConfig(lr=1e-2, warmup_steps=2, max_steps=6, batch_size=4)
seed_everything(1234); ref_model = GPT(ModelConfig())
ref = train(train_config=cfg, model=ref_model, train_bin=bin_path, val_bin=val_path,
            return_final_loss=True)
# ... run half → checkpoint_path=ckpt → KILL → fresh GPT → resume_from=ckpt ...
assert abs(float(resumed) - float(ref)) < 1e-6
```
Note: cross-device bitwise determinism is NOT guaranteed on MPS (RESEARCH A5) — this resume test stays **CPU-only** (the determinism oracle); MPS is validated only by `test_mps_smoke.py`.

---

### `tests/test_best_ckpt.py` (NEW — best-val tracking + perplexity, CPU-only)

**Analog:** `tests/test_resume_curve.py` (its `torch.load(ckpt, weights_only=False)` blob-inspection idiom, lines 183-184) + `checkpoint.py` save/load (`val_loss` field at `checkpoint.py:64`).

**Inspect the saved checkpoint's `val_loss`** (copy the blob-read idiom `test_resume_curve.py:183-184`):
```python
blob = torch.load(best_path, weights_only=False)   # own trusted file
assert blob["val_loss"] == pytest.approx(min_observed_val_loss)
```

**Tests to write:** `best.pt` holds the run's **lowest** val loss (drive a run where val loss dips then rises; assert best.pt captured the dip, not the final step); `perplexity == exp(best_val_loss)` is the recorded PRE-03 figure. CPU-only, GPU/MPS-free.

---

## Shared Patterns

### Device / precision resolution (single source of truth — ALREADY LANDED, D-02)
**Source:** `src/personacore/config.py::RuntimeConfig` (`_default_device` lines 21-32; MPS→fp32 in `__post_init__` lines 55-59) + `src/personacore/preflight.py::preflight_device` (lines 25-81).
**Apply to:** every new file that touches a device. **Consume, never re-implement.**
- Loop/data/scripts read `runtime.device` only — NEVER call `torch.backends.mps.*` or `torch.cuda.*` directly (anti-pattern, RESEARCH). The one allowed exception is the `skipif` guard in `test_mps_smoke.py`.
- MPS forces `amp=False` automatically; there is no scaler/fp16 path to add this phase.
```python
def _default_device() -> str:
    if torch.cuda.is_available(): return "cuda"
    if torch.backends.mps.is_available(): return "mps"
    return "cpu"
```

### Frozen-tokenizer reuse (NEVER `.train()` — Pitfall 6)
**Source:** `src/personacore/training/data.py:32` + `src/personacore/tokenizer/__init__.py` (`from_json`).
**Apply to:** `encode_corpus.py`, `pretrain_tinystories.py`, `test_memmap_data.py`.
```python
tok = from_json("artifacts/tokenizer.json")          # FROZEN — never retrain (Pitfall 6)
ids = tok.encode(text, allowed_special="all")        # <|endoftext|> → atomic 8184
```

### `uint16` storage, `int64` only at batch time
**Source:** `data.py::load_split` (lines 53-54) + `data.py::get_batch` (lines 66-68).
**Apply to:** `encode_corpus.py` (store `np.uint16`), `get_batch_memmap` (cast `.astype(np.int64)` at draw time). vocab 8192 < 65536 fits `uint16`.

### Resumable open-dict checkpoint (full RNG restore)
**Source:** `src/personacore/checkpoint.py::save_checkpoint`/`load_checkpoint` (lines 32-111).
**Apply to:** loop Seams 3 & 4 (best.pt + periodic latest.pt) and the resume/best-ckpt tests.
- `save_checkpoint(...)` already accepts `val_loss=` (line 64) and arbitrary `**extra` (line 75) — best.pt needs NO format change.
- Resume uses `weights_only=False` on OWN trusted files only (`checkpoint.py:95`); the Phase-8 slim ckpt will use `weights_only=True`.

### Thin `scripts/` entry, no CLI/argparse (Phase-1 D-04)
**Source:** `scripts/train_bigram.py` (lines 14-27, 65-72), `scripts/preflight_demo.py`.
**Apply to:** both new scripts — `_REPO_ROOT`-relative path constants, `def main()`, `if __name__ == "__main__": main()`, no argparse. Logic lives in `src/personacore/`; scripts only wire configs + paths + print.

### CPU-only test suite + skipif device guard
**Source:** `tests/test_data_split.py` / `tests/test_resume_curve.py` (CPU-only) + `tests/test_preflight.py` (monkeypatch device) + `tests/conftest.py` (`simulate_pascal`).
**Apply to:** all 4 new tests. Three are pure CPU; only `test_mps_smoke.py` carries `@pytest.mark.skipif(not torch.backends.mps.is_available())` and is the sole MPS-touching test.

---

## No Analog Found

None. Every new/modified surface has a direct in-repo analog (Phase 5 is ~90% reuse). The genuinely
new *content* is small and bounded — the streaming encode mechanics (RESEARCH Pattern 1), the
memmap re-open-per-batch leak-avoidance (Pattern 2), and the empirical calibration numbers
(LR/batch/grad_accum/steps) — but each rides on an existing structural analog above. The
calibration LR/batch/step values are deliberately UNRESOLVED (RESEARCH Open Q1) and are produced by
the calibration smoke, not copied from any analog.

## Metadata

**Analog search scope:** `src/personacore/{training,model,tokenizer}/`, `src/personacore/{config,checkpoint,preflight}.py`, `scripts/`, `tests/`.
**Files scanned (read in full):** `training/data.py`, `training/loop.py`, `training/__init__.py`, `checkpoint.py`, `config.py`, `preflight.py`, `model/gpt.py`, `tokenizer/__init__.py`, `scripts/preflight_demo.py`, `scripts/train_bigram.py`, `tests/test_resume_curve.py`, `tests/test_gpt_overfit.py`, `tests/test_data_split.py`, `tests/test_preflight.py`, `tests/conftest.py`; grepped `tokenizer/bpe.py` (encode sig), `.gitignore`.
**Pattern extraction date:** 2026-06-05
