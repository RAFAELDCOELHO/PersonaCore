# Phase 5: TinyStories Pretraining - Research

**Researched:** 2026-06-05
**Domain:** From-scratch GPT pretraining on TinyStories — full-corpus `uint16` memmap data path, resumable long run on Apple Silicon (MPS, fp32), best-val-loss checkpoint + recorded curves/perplexity
**Confidence:** HIGH (codebase reuse + nanoGPT memmap pattern + TinyStories paper); MEDIUM on the empirical M3/MPS throughput numbers (must be measured by the calibration smoke this phase prescribes — not pre-decided)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Add MPS as a real training device and produce the shipped checkpoint **locally on M3/MPS**, REPLACING the Kaggle P100 run. Kaggle becomes optional/unused. Training (not just inference) runs on the user's own machine — the strongest "fully on-device, zero-budget, privacy-by-design" expression.
- **D-01a — risks acknowledged & accepted:** MPS op-coverage/correctness gaps (possible silent NaNs or CPU fallbacks on some ops), **no fp16-AMP memory win (fp32 only)**, laptop wall-clock/thermal limits. None fatal at 13.9M params. **Add a cheap MPS sanity gate (overfit-one-batch smoke + finite-loss assertion) before the long run.**
- **D-02 — device-layer API change (do NOW, before planning Phase 5):** `preflight_p100` → `preflight_device` with priority **CUDA-P100 → MPS → CPU**; `RuntimeConfig` detects `torch.backends.mps.is_available()` and resolves `device="mps"`; **MPS forces fp32 + AMP disabled**; bf16-on-Pascal guard unchanged; hard rename (no deprecated alias); P100 detection kept available under the new priority order. **→ VERIFIED ALREADY LANDED — see "D-02 Verification" below.**
- **D-03:** Train on the **full TinyStoriesV2-GPT4 corpus** (~500–550M tokens, ~2.23 GB raw). Calibration sizes epochs/steps to local budget.
- **D-04:** **Quality-first / "as long as it takes."** No fixed wall-clock cap; run until the fluency bar is met (D-06), leaning on resumable checkpoints across sessions.
- **D-05:** Held-out val = the **official TinyStoriesV2-GPT4 `valid` file** (~22.5 MB) — zero leakage by construction.
- **D-06:** **Stop on validation-loss plateau + periodic qualitative sample checks.**
- **D-07:** Acceptance bar (PRE-02) = **BOTH** a recorded perplexity figure (PRE-03) **AND** curated samples that read as coherent TinyStories-register text.
- **D-08:** Ship the **best-val-loss checkpoint** (track lowest val loss, not necessarily the final step).
- **D-09:** **Encode once, locally.** Load frozen `artifacts/tokenizer.json` (never retrain), encode full train → `train.bin`, official valid → `val.bin` as flat `np.uint16` memmaps, **one EOS (8184) between documents**, gitignored local disk. Add a full-corpus `np.memmap` `get_batch` path alongside the existing bounded-fixture `load_split`; keep the fixture path for tests.

### Claude's Discretion

- Memmap build script location/shape (thin `scripts/` entry, **no CLI/argparse** — Phase-1 D-04), checkpoint cadence (every K steps), best-checkpoint tracking mechanism, sample-generation cadence during training, calibration smoke harness — delegated to research/planning.
- Empirical **LR / batch / steps / block-size-for-MPS** values are the **calibration study's output** (this research's protocol), not pre-decided here.

### Deferred Ideas (OUT OF SCOPE)

- **REQUIRED rewording (NOT optional — consequence of D-01):** `.planning/REQUIREMENTS.md` PRE-01/PRE-02, `.planning/ROADMAP.md` Phase-5 success criteria #1/#2, `PROJECT.md`/`CLAUDE.md`/`STACK.md` "train on Kaggle P100" → "train on M3/MPS (Kaggle P100 optional fallback)". (Note: ROADMAP and REQUIREMENTS already carry the reworded M3/MPS-primary text as of 2026-06-05; the ROADMAP Phase-5 line item #20 still says "full Kaggle P100 run" and is the last stale string to fix.)
- fp16 AMP / sdpa for memory — moot on MPS (fp32 only).
- KV-cache for CPU/MPS inference latency — Milestone 2 / Phase 8.
- Architecture / LR ablation table — Phase 7 (EVAL-03).
- Full `generate()` (top-k/top-p, EOS-stop) — Phase 6 (GEN-01..03). **Phase 5 uses ONLY the minimal `sample()` already in `loop.py` for periodic qualitative checks.**
- Retraining the tokenizer — frozen `artifacts/tokenizer.json` reused unchanged.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| **PRE-01** | TinyStories obtained, encoded once from the frozen tokenizer into a `uint16` memmap (`train.bin`/`val.bin`, one EOS between documents), persisted on local disk; official `valid` file is the no-leakage held-out set. | "Memmap Build Mechanics" (streaming encode → `np.uint16` memmap), "Standard Stack" (download URLs, `np.memmap`), "Don't Hand-Roll" (no doc-carving split — use the official `valid`). Validation: round-trip + one-EOS-between-docs + no-leakage tests. |
| **PRE-02** | Pretrained to fluent/coherent generation, producing a trained checkpoint; primary run on local M3/MPS (fp32, quality-first, resumable across sessions). | "M3/MPS Practical Reality" (throughput, op-coverage pitfalls, sanity gate), "Calibration Protocol" (sizing LR/batch/accum/steps), "Token Budget" (how many tokens reach the coherence bar), reuse of `train(...)` resumable loop. |
| **PRE-03** | Final/val perplexity + training curves recorded for the writeup. | "Best-Val-Loss Tracking & Perplexity" (`ppl = exp(val_loss)`), reuse of `CSVLogger` + the `val_loss` curve column; "Validation Architecture" (perplexity is the recorded acceptance number). |
</phase_requirements>

## Summary

Phase 5 produces **the** shipped checkpoint by pointing the already-proven `train(...)` loop at a full-corpus TinyStories memmap and running it to coherence on Apple Silicon (MPS, fp32). The heavy infrastructure already exists and is reused unchanged: the AMP/accum/clip step ordering, RNG-snapshot validation, resumable open-dict checkpoints (full RNG restore → bit-for-bit resume across session kills), the restart-safe CSV logger, the frozen tokenizer, and `RuntimeConfig`/`preflight_device` MPS support (**D-02 is verified already landed**). The genuinely **new** work is small and well-bounded: (1) a streaming **memmap build script** (`scripts/`, no CLI) that encodes the ~2.23 GB corpus once into `train.bin`/`val.bin` with one EOS between docs; (2) a **full-corpus `np.memmap` `get_batch` path** in `training/data.py` mirroring the existing in-RAM sampler (nanoGPT idiom: re-open the memmap each batch to avoid a leak); (3) **best-val-loss checkpoint tracking** + **periodic qualitative sampling** woven into the loop with minimal additions; (4) a **calibration/smoke protocol** that *measures* tokens/sec and coherence-per-hour on MPS rather than guessing hyperparameters.

The model is a ~13.9M-param GPT (6L/6H/384d, `block_size=256`, `vocab=8192`, `eos=8184`). The closest public reference — an 8M-param GPT (8L/8H/128d, block 256, bs 12, lr 5e-4) — reached **val loss ≈ 1.99** training ~2 epochs (~35k iters) over **~2 days on an M1 CPU** with only moderate coherence. The PersonaCore model is wider (384d) and runs on the MPS GPU (2–3× faster than M1 CPU per the nanoGPT MPS note), so it should reach a **lower val loss faster**; the TinyStories paper's own ~8.3M model hit GPT-4 grades of ~8/10 grammar, so the architecture is capable of clearing the coherence bar. These are MEDIUM-confidence anchors — the calibration smoke must convert them into the actual LR/batch/step numbers.

**Primary recommendation:** Build the streaming memmap encode script + the `np.memmap` `get_batch` path; add a `best_val_loss`-tracked `best.pt` save and a periodic-sample hook to the loop; run the calibration smoke (a few hundred steps, measure tokens/sec + finite-loss + first coherence signal) to set LR/batch/grad_accum; then launch the resumable long run quality-first, shipping the best-val-loss checkpoint with `perplexity = exp(best_val_loss)` and the CSV curves recorded.

## D-02 Verification (device-layer prerequisite — IS IT ACTUALLY IN THE CODE?)

**VERIFIED LANDED.** Read of `src/personacore/config.py` and `src/personacore/preflight.py` confirms all of D-02:

| D-02 sub-item | Status | Evidence |
|---------------|--------|----------|
| `preflight_p100` → `preflight_device`, priority CUDA-P100 → MPS → CPU | ✅ DONE | `preflight.py:25` `def preflight_device(strict=True)`; CUDA branch (P100 name check + Pascal smoke op), MPS branch (returns, never raises), CPU branch (raises iff `strict`). |
| `RuntimeConfig` detects MPS, resolves `device="mps"` | ✅ DONE | `config.py:21-32` `_default_device()` returns `"mps"` when `torch.backends.mps.is_available()`. |
| MPS forces fp32 + AMP disabled | ✅ DONE | `config.py:55-59` `__post_init__`: `if self.device in ("cpu","mps"): self.amp = False`. |
| bf16-on-Pascal guard unchanged | ✅ DONE | `config.py:60-65` still raises on `amp_dtype=="bfloat16"` + `_is_pascal`. |
| Hard rename, callers/tests updated | ✅ DONE | git log shows `bddbbd7 hard-rename preflight_p100 -> preflight_device`, `a3513e8 update preflight_demo caller`, `450d54d MPS device-layer support`. `scripts/preflight_demo.py` references `preflight_device`. |

**Implication for the planner:** D-02 is NOT Phase-5 work — it is a completed prerequisite. Phase 5 plans should *consume* `preflight_device`/MPS-aware `RuntimeConfig`, not re-implement them. One residual gap to watch: `scripts/preflight_demo.py` still documents a Kaggle `DATA_DIR=/kaggle/input/...` mount convention (P100-era); the Phase-5 run entry script should preflight the **local** memmap paths, not the Kaggle mount.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Corpus download + one-time encode → memmap | Data-prep script (`scripts/`, offline, run-once) | `training/data.py` (memmap reader) | Encoding is a one-shot offline transform; it must NOT live in the hot training path. Output is the `train.bin`/`val.bin` contract. |
| Random-window batch sampling | `training/data.py` (`get_batch` memmap path) | — | Corpus-size-agnostic sampler; the only change is swapping the in-RAM array for `np.memmap`. |
| Device/precision resolution | `RuntimeConfig` (single source of truth) | `preflight_device` (assert before run) | Already MPS-aware (D-02). Nothing in the loop calls `torch.backends.mps.*` directly. |
| Train-step orchestration (AMP/accum/clip/sched) | `training/loop.py::train` | — | Reused unchanged; fp32-on-MPS path already runs (scaler disabled). |
| Resumability (kill → resume bit-for-bit) | `checkpoint.py` (open-dict, full RNG restore) | `loop.py` (`resume_from`) | Existing infra gives D-04 "as long as it takes" for free. |
| Best-val-loss tracking + best.pt | `training/loop.py` (new minimal addition) | `checkpoint.py` (reused saver) | D-08 needs lowest-val tracking; the saver already exists, only the "when to save best" branch is new. |
| Periodic qualitative sampling | `training/loop.py` (minimal hook over existing `sample()`) | — | D-06 needs periodic generations; the minimal `sample()` is already in `loop.py`. NO Phase-6 `generate()`. |
| Curve + perplexity recording | `logging.py::CSVLogger` (reused) | `demo.ipynb` (Phase 8 reads it) | `val_loss` column already exists; perplexity = `exp(val_loss)` is a derived number for the writeup. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `torch` | local M3 wheel with MPS backend (`2.7.*` pinned per CLAUDE.md; any `>=2.7` macOS wheel exposes MPS) | training compute on MPS fp32, autograd, AdamW, save/load | Already the project's framework; MPS backend is the shipped training device (D-01). `[CITED: pytorch.org/get-started/locally]` |
| `numpy` | 2.x (`>=1.26,<3`) | `np.uint16` memmap corpus + random-window sampling | nanoGPT-standard `.bin` token store; `np.memmap` reads are RAM-light over a 2.23 GB corpus. `[CITED: github.com/karpathy/nanoGPT]` |
| `personacore` (frozen tokenizer) | `artifacts/tokenizer.json` (vocab 8192, eos 8184) | encode corpus once | FROZEN — `from_json(...)`, never `.train()`. `[VERIFIED: codebase src/personacore/tokenizer/io.py:56]` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `tqdm` | 4.66+ (already a dep) | progress bar for the long streaming-encode loop and the training loop | The encode over ~500M tokens is long; a progress bar is humane. Optional. |
| `requests` | 2.32+ (already an optional dep) | one-time download of the two TinyStoriesV2 `.txt` files | Only for the encode script; not a runtime training dep. Or `curl`/`wget` manually. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `np.memmap` flat `uint16` `.bin` | HF `datasets` streaming | Heavy dependency + implicit network during training; violates offline/from-scratch intent. NOT at TinyStories scale. |
| Official `valid` file as held-out (D-05) | Carve val docs out of train | The official `valid` is non-overlapping by construction — zero leakage with zero code. Carving needs a doc-boundary split + leakage proof. Use the official file. |
| `np.memmap(mode='r')` reader | Load whole `train.bin` into RAM | ~1 GB (`uint16` × ~500M) fits in 16 GB but competes with model/activations; memmap is the safe nanoGPT default and lets the OS page-cache. |

**Installation:** No new packages required for training. For the one-time encode script, optionally:
```bash
# already-present deps cover this; requests only if downloading in-script
pip install "tqdm>=4.66" "requests>=2.32"   # both already declared in the project
```

**Data download (one-time, offline thereafter):**
```bash
# TinyStoriesV2-GPT4 (GPT-4-only corpus — higher coherence-per-param than the mixed V1)
curl -L -o data/TinyStoriesV2-GPT4-train.txt \
  https://huggingface.co/datasets/roneneldan/TinyStories/resolve/main/TinyStoriesV2-GPT4-train.txt
curl -L -o data/TinyStoriesV2-GPT4-valid.txt \
  https://huggingface.co/datasets/roneneldan/TinyStories/resolve/main/TinyStoriesV2-GPT4-valid.txt
# train ~2.23 GB, valid ~22.5 MB; plain UTF-8, documents separated by <|endoftext|>
```
`[CITED: huggingface.co/datasets/roneneldan/TinyStories/tree/main]` — URLs verified in CLAUDE.md Sources and `scripts/train_tokenizer.py:17`. `data/` is gitignored. **Note:** WebFetch could not hit the HF resolve URL in-session to confirm live byte sizes; sizes are `[CITED]` from CLAUDE.md, treat as MEDIUM until the download runs.

**Version verification:** `torch` is not importable in the research sandbox (no venv active here); the planner/executor must run inside the mandatory Python 3.11 venv where `torch` + MPS resolve. `[ASSUMED]` that the venv's macOS wheel exposes a working MPS backend — the preflight + finite-loss smoke gate (below) is exactly what confirms this before the long run.

## Package Legitimacy Audit

> Phase 5 installs **no new external packages** for the training path. `torch`, `numpy`, `tqdm`, `requests` are all pre-declared, established project dependencies vetted in earlier phases. No slopcheck run required (nothing new to install).

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| torch | PyPI | 8+ yrs | very high | github.com/pytorch/pytorch | n/a (pre-existing) | Already approved (Phase 1) |
| numpy | PyPI | 15+ yrs | very high | github.com/numpy/numpy | n/a (pre-existing) | Already approved (Phase 1) |
| tqdm | PyPI | 9+ yrs | very high | github.com/tqdm/tqdm | n/a (pre-existing) | Already declared |
| requests | PyPI | 13+ yrs | very high | github.com/psf/requests | n/a (pre-existing) | Already declared (optional) |

**Packages removed due to slopcheck [SLOP] verdict:** none.
**Packages flagged as suspicious [SUS]:** none.

## Architecture Patterns

### System Architecture Diagram

```
[one-time, offline]
 TinyStoriesV2-GPT4-train.txt (2.23GB) ──┐
 TinyStoriesV2-GPT4-valid.txt (22.5MB) ──┤
                                          │
                  scripts/encode_corpus.py (NO CLI, run-once)
                   │  load frozen tokenizer.json (never .train())
                   │  stream chunks → encode → append uint16 ids
                   │  one EOS(8184) between documents
                   ▼
        data/train.bin   data/val.bin   (flat np.uint16 memmaps, gitignored)
                   │                │
                   │                │  (read-only, re-opened per batch)
                   ▼                ▼
       training/data.py :: get_batch_memmap(path, bs, block, device)
                   │  random offsets ∈ [0, len-block-1] ; uint16→int64 at batch time
                   ▼
       training/loop.py :: train(...)   [REUSED, fp32 on MPS]
         ├─ RuntimeConfig → device="mps", amp=False (D-02, verified)
         ├─ AdamW + warmup/cosine + grad-clip + grad-accum (unchanged)
         ├─ every eval_interval: estimate_loss(val) → val_loss
         │     ├─ NEW: if val_loss < best_val_loss → save best.pt  (D-08)
         │     └─ NEW: periodic sample() → print decoded story  (D-06 coherence check)
         ├─ CSVLogger append (step,train_loss,val_loss,lr,tokens) [REUSED, restart-safe]
         └─ save_checkpoint latest.pt every K steps / on kill [REUSED → resumable]
                   │
                   ▼  (kill at session end → resume_from=latest.pt restores RNG bit-for-bit)
        best.pt (lowest val loss) ──► Phase 6 generate() / Phase 8 slim ckpt
        run.csv  + perplexity=exp(best_val_loss) ──► Phase 7 eval / Phase 8 demo.ipynb
```

### Recommended Project Structure (only NEW/changed files)
```
scripts/
└── encode_corpus.py      # NEW: one-time streaming encode → train.bin/val.bin (no CLI, Phase-1 D-04)
                          # (a thin train entry script, e.g. pretrain_tinystories.py, may also be added)
src/personacore/training/
└── data.py               # CHANGED: + get_batch over np.memmap (full-corpus path) alongside load_split/get_batch
src/personacore/training/
└── loop.py               # CHANGED (minimal): + best_val_loss tracking/best.pt save; + periodic sample hook;
                          #   + a memmap data-source branch (point train() at train.bin/val.bin)
data/                     # gitignored: TinyStoriesV2-GPT4-*.txt, train.bin, val.bin
checkpoints/, logs/       # gitignored: latest.pt, best.pt, run.csv
tests/
├── test_memmap_data.py   # NEW: round-trip, one-EOS-between-docs, in-bounds get_batch, no-leakage
└── test_best_ckpt.py     # NEW: best.pt tracks the lowest val loss (CPU-only, GPU/MPS-free)
```

### Pattern 1: Streaming encode → `uint16` memmap (nanoGPT idiom, scaled to 2.23 GB)
**What:** Encode the corpus once, never re-tokenize during training. Store as a flat `np.uint16` array on disk.
**When to use:** PRE-01 corpus prep.
**Key mechanic (avoid OOM on 2.23 GB):** Do NOT read the whole 2.23 GB file into one Python string and encode it in one call. Stream by document (split on `<|endoftext|>`), encode each, append ids with **one EOS between documents**, and write incrementally. nanoGPT writes the final array with `np.ndarray.tofile(...)`; for a corpus that doesn't fit comfortably in RAM as a Python list of ints (~500M ints ≈ 4 GB as a Python list, but only ~1 GB as `uint16`), pre-size an `np.memmap(..., mode='w+', dtype=np.uint16, shape=(N,))` and fill it in chunks, OR accumulate `uint16` numpy arrays per shard and concatenate. Simplest robust approach:
```python
# Source pattern: github.com/karpathy/nanoGPT data prepare + per-doc streaming
# (illustrative — executor adapts to the frozen tokenizer's encode signature)
import numpy as np
from personacore.tokenizer import from_json

EOS = 8184
tok = from_json("artifacts/tokenizer.json")          # FROZEN — never .train()

def encode_to_bin(txt_path, bin_path):
    # Pass 1 (optional): count tokens to pre-size the memmap. Or buffer shards then concat.
    shards = []
    with open(txt_path, encoding="utf-8") as fh:
        buf = []
        for line in fh:                               # stream; never read 2.23GB at once
            buf.append(line)
            if "<|endoftext|>" in line:               # document boundary
                doc = "".join(buf)
                ids = tok.encode(doc, allowed_special="all")  # <|endoftext|> → atomic 8184
                shards.append(np.asarray(ids, dtype=np.uint16))
                buf = []
        if buf and "".join(buf).strip():              # content-bearing tail w/o trailing EOS
            ids = tok.encode("".join(buf), allowed_special="all")
            shards.append(np.asarray(ids, dtype=np.uint16))
    arr = np.concatenate(shards)                      # one stream; EOS already terminates each doc
    arr.tofile(bin_path)                              # flat uint16 .bin (nanoGPT format)
```
**Note on EOS placement:** TinyStories docs are *already* `<|endoftext|>`-separated in the raw text, and `tok.encode(..., allowed_special="all")` maps that marker to the atomic `8184` (verified: `data.py:35` relies on exactly this). So "one EOS between documents" is satisfied by the source format + atomic encoding — do NOT also manually inject extra EOS ids (that would double them). The executor must assert: count of `8184` in `train.bin` ≈ number of documents.
`[VERIFIED: codebase src/personacore/training/data.py:35 + tokenizer allowed_special]`

### Pattern 2: `np.memmap` `get_batch` (re-open per batch to avoid the leak)
**What:** The full-corpus sampler mirrors the existing in-RAM `get_batch` but reads from a memmap.
**When to use:** the long run's data source.
**Critical mechanic:** **re-create the `np.memmap` inside `get_batch` every call** — a long-lived memmap iterated across thousands of batches leaks memory (documented nanoGPT gotcha). The existing `get_batch(arr, ...)` takes an in-RAM array; the memmap variant takes a *path*:
```python
# Source: github.com/karpathy/nanoGPT train.py get_batch (the "recreate np.memmap every batch
# to avoid a memory leak" pattern). Mirrors the existing data.py::get_batch indexing exactly.
def get_batch_memmap(bin_path, batch_size, block_size, device):
    data = np.memmap(bin_path, dtype=np.uint16, mode="r")   # re-open EACH call (no leak)
    ix = np.random.randint(0, len(data) - block_size - 1, size=batch_size)
    x = torch.stack([torch.from_numpy(data[i:i+block_size].astype(np.int64)) for i in ix])
    y = torch.stack([torch.from_numpy(data[i+1:i+1+block_size].astype(np.int64)) for i in ix])
    return x.to(device), y.to(device)                       # uint16→int64 at batch time
```
This is line-for-line the existing `data.py::get_batch` indexing (same `len-block-1` bound, same `uint16→int64` cast) with `arr` replaced by a freshly-opened memmap. **`pin_memory()`/`non_blocking` is CUDA-only** — on MPS/CPU use the plain `.to(device)` already in the existing `get_batch`. `[VERIFIED: nanoGPT get_batch + codebase data.py:58-70]`

### Pattern 3: Wiring the memmap path into `train(...)` (minimal seam change)
**What:** `train()` already has a 3-mode data branch (`fixed_batch` / `corpus_path` / synthetic). Add a 4th: a memmap source. Cleanest approach that respects "minimal new code": pass `train_bin_path`/`val_bin_path` (or reuse `corpus_path` to point at a `.bin` and branch on extension), build `batch_fn` from `get_batch_memmap`, and set `val_ids` to the val memmap path so `estimate_loss` uses it. `estimate_loss` currently takes an in-RAM `val_ids` array and calls `get_batch(val_ids,...)`; the memmap path needs `estimate_loss` to accept a path + use `get_batch_memmap` (small, localized change). `[VERIFIED: codebase loop.py:60-81, 197-231]`

### Pattern 4: Best-val-loss tracking + periodic sampling (D-06/D-08)
**What:** At each eval, compare `val_loss` to a running `best_val_loss`; when lower, `save_checkpoint(best_path, ..., val_loss=val_loss)`. Independently, every `sample_interval` steps, run the existing minimal `sample()` from a short seed and print the decoded text for the qualitative coherence check.
**Minimal additions to `loop.py`:**
- a `best_val_loss = float("inf")` local + a `best_checkpoint_path` kwarg; inside the eval branch: `if val_loss < best_val_loss: best_val_loss = val_loss; save_checkpoint(best_checkpoint_path, ...)`.
- a `sample_interval`/`sample_prompt` kwarg; periodically `print(tok.decode(sample(model, seed_idx, max_new_tokens=...)[0].tolist()))`.
Both are additive and don't touch the load-bearing AMP/accum/resume ordering. `[VERIFIED: codebase loop.py sample() at :84-98, save_checkpoint reuse]`

### Anti-Patterns to Avoid
- **Re-tokenizing in the training loop:** never call `tok.encode` per batch — encode once to `.bin`. (Defeats the memmap purpose, slow.)
- **Long-lived memmap object:** keeping one `np.memmap` for the whole run leaks; re-open per batch.
- **Manually injecting extra EOS:** the source already separates docs with `<|endoftext|>`; double-EOS corrupts the doc-boundary statistics.
- **Carving val out of train:** use the official `valid` file (D-05) — zero-leakage for free.
- **Calling `torch.backends.mps.*` outside `RuntimeConfig`:** the single-source-of-truth rule (config.py owns device). Loop/data only see `runtime.device`.
- **Using Phase-6 `generate()`:** it doesn't exist yet — Phase 5's periodic check uses the minimal `sample()` already in `loop.py`.
- **fp16/AMP/GradScaler on MPS:** `RuntimeConfig` already disables AMP on MPS; don't reintroduce a scaler path (no benefit, no fp16 on MPS).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Resumable training across session kills | A new checkpoint/resume system | `checkpoint.py` (open-dict, full RNG restore) + `loop.py` `resume_from` | Already gives bit-for-bit resume (tested in `test_resume_curve.py`); D-04 "as long as it takes" is free. |
| Restart-safe curve logging | A new logger / wandb | `logging.py::CSVLogger` | Append-only, header-once, restart-survivable; already exercised. wandb violates offline/zero-budget. |
| LR schedule | New warmup/cosine code | `schedule.py::build_scheduler` | Resumable LambdaLR contract already serialized in the checkpoint. |
| Random-window batching | New sampler | `data.py::get_batch` indexing (swap array→memmap) | Same in-bounds bound + `uint16→int64` cast; only the source changes. |
| No-leakage val split | Doc-boundary carving + leakage proof | The official `valid` file (D-05) | Non-overlapping by construction; zero code, zero risk. |
| Tokenization | Re-train / re-implement BPE | Frozen `artifacts/tokenizer.json` via `from_json` | Frozen production artifact; retraining would invalidate the locked vocab. |
| Device/precision resolution | `torch.backends.mps` checks scattered in loop | `RuntimeConfig` (D-02, verified) | Single source of truth; MPS→fp32 already wired. |
| Periodic generation (Phase 5) | A full sampler | The minimal `sample()` in `loop.py` | Phase 5 only needs a qualitative "does it read as a story" check; the rich `generate()` is Phase 6. |

**Key insight:** Phase 5 is ~90% reuse. The only genuinely new code is the **encode script**, the **memmap `get_batch`**, **best-val tracking**, and a **periodic-sample print** — plus the *measurement discipline* of the calibration smoke. Resist re-architecting the loop.

## Runtime State Inventory

> Phase 5 is greenfield data/training, not a rename/refactor — but it does introduce new on-disk state. The relevant inventory:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | NEW: `data/train.bin`, `data/val.bin` (uint16 memmaps), `data/TinyStoriesV2-GPT4-*.txt` (raw). | Encode once; all gitignored (`data/` already in `.gitignore`). Verified `data/` is empty now. |
| Build artifacts / checkpoints | NEW: `checkpoints/latest.pt`, `checkpoints/best.pt`, `logs/run.csv`. | gitignored (`checkpoints/`, `*.pt`, `logs/` already covered). |
| Live service config | None — fully local/offline, no external services. | None. |
| OS-registered state | None — no schedulers/daemons; the long run is a foreground/`nohup` process the user manages. | None. |
| Secrets/env vars | None — no Kaggle token needed (Kaggle path unused per D-01). | None. The P100-era `preflight_demo.py` Kaggle mount doc is now vestigial. |

**Verified:** `.gitignore` covers `data/`, `checkpoints/`, `*.pt`, `logs/` — no new gitignore entries needed.

## M3/MPS Practical Reality (Open Q2)

**Throughput (MEDIUM — must be measured, not assumed):** The closest public data point is an 8M GPT (8L/8H/128d, block 256, bs 12) at **~600–632 ms/iter on an M1 CPU**. The PersonaCore model is wider (384d vs 128d → ~roughly 4–8× the FLOPs/step depending on batch), but runs on the **MPS GPU** which the nanoGPT docs report as **2–3× faster than M1 CPU** (and an M3 GPU is materially faster than M1). Net: expect *somewhere in the same order* of hundreds of ms/iter at a comparable batch — but this is exactly what the calibration smoke must measure. **Do not hardcode a step budget from these numbers; measure tokens/sec on the actual machine.** `[CITED: medium.com replicating-tinystories + github.com/karpathy/nanoGPT issue #28]`

**Op-coverage / correctness pitfalls (D-01a):**
- **Silent CPU fallback:** some ops aren't implemented on MPS and silently fall back to CPU (or, in older torch, error). Set `PYTORCH_ENABLE_MPS_FALLBACK=1` so a missing op falls back to CPU instead of crashing the long run — but log a warning, because frequent fallbacks tank throughput. `[ASSUMED]` — verify against the active torch version's MPS op coverage; the model here is plain `nn.Linear`/`Embedding`/`LayerNorm`/`softmax`/`gelu`/`cross_entropy`, all of which are well-covered on MPS, so fallbacks should be rare.
- **Silent NaN / numerical divergence:** the cheapest reliable gate is the **finite-loss assertion** — after the first forward/backward on MPS, assert `torch.isfinite(loss)`. Combine with the **overfit-one-batch smoke** (D-01a): run the existing overfit pattern on `device="mps"` for ~100 steps and assert loss drives toward zero. If MPS produces NaNs or fails to overfit while CPU does, that's the early-warning signal to fall back to CPU for the run.
- **`float("-inf")` in the manual attention mask:** the hand-rolled attention does `masked_fill(..., float("-inf"))` then `softmax` — this is fine on MPS in fp32 (it's the standard pattern), but the finite-loss gate covers any edge case.
- **Determinism:** MPS RNG/determinism is weaker than CPU. The resume contract is still satisfied because the checkpoint restores RNG *state*; but bit-for-bit cross-device reproduction (MPS vs CPU) is not guaranteed. Keep the CPU-only test suite as the determinism oracle; the MPS run is validated by the finite-loss + overfit smoke, not bitwise equality. `[ASSUMED]`

**block_size/batch × unified memory:** MPS uses unified memory (no host↔device copy), so the 16 GB (or more on M3) is shared between OS, model, and activations. At 13.9M params fp32 (~56 MB weights + ~56 MB AdamW moments ×2) the model is tiny; the budget is **activations = batch × block_size × n_embd × n_layer**. `block_size` is locked at 256 (the model's trained context). The free lever is **batch_size × grad_accum_steps**: pick the largest `batch_size` that keeps a comfortable memory margin, then use `grad_accum_steps` to reach a larger *effective* batch without more peak memory. The calibration smoke measures the largest stable batch.

**Cheapest reliable MPS sanity gate (the D-01a requirement), concretely:**
1. `preflight_device(strict=True)` → asserts MPS is the active device.
2. Overfit-one-batch on MPS for ~100 steps → loss → ~0 (reuses the existing overfit gate, just `device="mps"`).
3. `assert torch.isfinite(loss)` after step 1 (finite-loss gate).
4. A ~200-step throughput probe on real `train.bin` → measure ms/iter + tokens/sec, confirm val loss decreases and a sampled story is non-garbage.
Only after all four pass does the long run launch.

## Memmap Build Mechanics (Open Q3)

- **Format:** flat `np.uint16` `.bin` (nanoGPT standard; `vocab=8192 < 65536` fits `uint16`). Two files: `train.bin` (from `TinyStoriesV2-GPT4-train.txt`), `val.bin` (from `TinyStoriesV2-GPT4-valid.txt`).
- **Streaming to avoid OOM:** the 2.23 GB raw → ~500–550M tokens → ~1.0–1.1 GB as `uint16`. Don't hold the whole corpus as a Python `list[int]` (~4 GB+). Stream per-document, encode, accumulate `uint16` numpy shards, `np.concatenate` (peak ~2× the final array), then `.tofile`. If even that is too much headroom, pre-size an `np.memmap(mode='w+')` and write shards by offset. At ~1 GB final on a 16 GB+ machine, `concatenate` is fine.
- **One EOS between docs:** satisfied by the source `<|endoftext|>` separators + atomic encoding to `8184`; assert post-build that `np.count_nonzero(arr == 8184)` ≈ document count. Do NOT add extra EOS.
- **Reader:** `get_batch_memmap` re-opens `np.memmap(path, dtype=np.uint16, mode='r')` per call (leak-avoidance), same indexing as the in-RAM `get_batch`.
- **Sanity round-trip:** decode the first ~200 tokens of `train.bin` back through the frozen tokenizer and eyeball a coherent story prefix; assert the first doc's tokens match `tok.encode(first_raw_doc)`.

## Token Budget & Expected Val Loss (Open Q5)

**Reference anchors (MEDIUM confidence — ballpark, not targets):**
- **TinyStories paper:** models *below 10M params* (embedding dim 256) produce fluent, consistent stories; their ~8.3M model scored GPT-4 grades ~8/10 grammar & consistency. Each 4× model-size increase ≈ 50% loss reduction / ~80% perplexity improvement. The 13.9M PersonaCore model (384d) is *above* the "fluent at <10M" threshold and wider than the paper's 256d, so the architecture is comfortably capable of the coherence bar. `[CITED: arxiv.org/abs/2305.07759]`
- **Community replication (8M, 8L/8H/128d, block 256, bs 12, lr 5e-4, dropout 0):** reached **val loss ≈ 1.99** after ~35k iters / ~2 epochs / ~2 days **on M1 CPU**, with grammatically-mostly-correct but only moderately coherent output (GPT-4 grade ~3/10 — below the paper's 8/10, attributed to the smaller width/undertraining). `[CITED: medium.com/@kl.yap replicating-tinystories]`

**What this implies for PersonaCore (the calibration must confirm):**
- The PersonaCore model is **wider (384d)** and runs on the **MPS GPU** (faster than M1 CPU). It should reach a **lower val loss** (likely **~1.5–1.8** territory, where TinyStories output reads as coherent) and do so in **fewer wall-clock hours** than the 2-day CPU run — but on a wider model each step costs more. Net wall-clock is genuinely uncertern; D-04 ("as long as it takes") + resumable checkpoints is the right posture.
- **Token budget ballpark:** the corpus is ~500–550M tokens. ~2 epochs (~1B tokens seen) is a reasonable *starting* budget per the 8M replication; the paper trains its small models to convergence on the same corpus. **Stop on val-loss plateau (D-06)**, not a fixed token count — but expect the order of **0.5–2 epochs** to reach coherence at this scale.
- **Perplexity:** record `perplexity = exp(best_val_loss)`. At val loss 1.99 → ppl ≈ 7.3; at 1.6 → ppl ≈ 5.0. The recorded number is the PRE-03 acceptance figure; coherent samples (D-07) are the qualitative half.

**Confidence:** MEDIUM. These are external anchors, not measurements of this exact config. The calibration smoke + the early epochs of the real run convert them into firm numbers.

## Calibration / Smoke Protocol (Open Q1 — the heart of the phase research flag)

The planner must NOT pre-decide LR/batch/steps. Instead, plan a **short calibration study** that *measures* them. Concrete protocol:

**Stage 0 — MPS sanity gate (must pass before anything long):**
- `preflight_device(strict=True)` → MPS active.
- Overfit-one-batch on `device="mps"` (~100 steps) → loss → ~0; `assert torch.isfinite(loss)`.

**Stage 1 — throughput + stability probe (~200–500 steps on real `train.bin`):**
- Fix `block_size=256` (locked). Sweep `batch_size ∈ {8,16,32,...}` to find the largest stable (no OOM, finite loss) batch on the machine; record **ms/iter** and **tokens/sec = batch×block_size / iter_time**.
- Confirm val loss decreases over the probe and a sampled story is non-garbage.

**Stage 2 — LR calibration (short runs, a few hundred steps each):**
- Anchor on the reference `lr=5e-4` (8M replication) and the project default `3e-4`. Try a small grid (e.g. `{3e-4, 5e-4, 1e-3}`) for ~300 steps each; pick the highest LR with smooth (non-diverging) loss. Warmup ~100 steps (existing default), cosine decay.
- Set `grad_accum_steps` so the **effective batch** (batch×accum) lands in a healthy range (the 8M ref used bs 12; effective ~256–512 tokens-per-step × is common — aim for effective batch in the tens-to-low-hundreds of sequences if memory allows, else accumulate).

**Stage 3 — size the run:**
- From measured tokens/sec, estimate wall-clock per epoch (≈ 500M tokens / tokens-per-sec). Set `max_steps` generously (D-04 quality-first); rely on val-plateau stopping (D-06) rather than a hard cap. Set `eval_interval` and checkpoint cadence (`K` steps) so a session kill loses ≤ a few minutes.

**Output the planner needs from calibration:** concrete `lr`, `batch_size`, `grad_accum_steps`, `eval_interval`, checkpoint-every-`K`, sample-every-`S`, and a measured tokens/sec → expected epoch wall-clock. These become the `TrainConfig` for the long run.

## Best-Val-Loss Tracking & Perplexity (D-08 / PRE-03)

- Track `best_val_loss` in the loop; on a new minimum, `save_checkpoint(best.pt, ..., val_loss=val_loss)`. `latest.pt` continues to save every K steps for resume. Ship `best.pt`.
- The CSV already logs the `val_loss` column every `eval_interval` — that *is* the recorded training curve (PRE-03). `demo.ipynb` (Phase 8) reads it. No new logging code.
- **Perplexity** = `exp(best_val_loss)`, recorded as the acceptance number. Per D-07, also curate a handful of generated samples at the best checkpoint that read as coherent TinyStories-register text.

## Common Pitfalls

### Pitfall 1: memmap memory leak over a long run
**What goes wrong:** Opening one `np.memmap` and slicing it across tens of thousands of batches grows RSS until OOM.
**Why:** numpy/OS page-cache + the long-lived mmap object accumulate.
**Avoid:** Re-create `np.memmap(..., mode='r')` *inside* `get_batch` every call (nanoGPT's documented fix). **Warning sign:** steadily climbing memory during training.

### Pitfall 2: silent MPS CPU-fallback or NaN
**What goes wrong:** An unsupported op silently runs on CPU (slow) or produces NaNs that quietly poison the run.
**Why:** MPS op coverage gaps (D-01a).
**Avoid:** `PYTORCH_ENABLE_MPS_FALLBACK=1` + the finite-loss assertion + the overfit-one-batch MPS smoke before the long run. **Warning sign:** loss → NaN, or throughput far below the probe.

### Pitfall 3: doubled or missing EOS between documents
**What goes wrong:** Either no separator (docs bleed together, model never learns story boundaries) or two EOS (skews boundary statistics).
**Why:** Manually injecting EOS on top of the source's `<|endoftext|>` separators, or stripping them.
**Avoid:** Trust the source separators + atomic encoding; assert `count(==8184) ≈ num_docs` post-build. **Warning sign:** generated stories never stop / never start cleanly.

### Pitfall 4: re-tokenizing or carving val from train (leakage)
**What goes wrong:** Val overlaps train → inflated (too-good) val loss, false coherence signal.
**Why:** Building val by slicing train, or re-encoding inconsistently.
**Avoid:** Use the official `valid` file (D-05). **Warning sign:** val loss suspiciously below train loss.

### Pitfall 5: checkpoint cadence too coarse for "as long as it takes"
**What goes wrong:** A laptop sleep/kill loses an hour of progress because `K` is huge.
**Why:** Checkpointing only at the end of `train()`.
**Avoid:** Save `latest.pt` every `K` steps inside the loop (the existing saver supports this — call it periodically, not just in the `finally`). **Note:** the current `loop.py` only saves at the end of the call; Phase 5 should add a periodic in-loop `save_checkpoint(latest.pt, ...)` every `K` steps (minimal addition). **Warning sign:** a kill costs > a few minutes of work.

### Pitfall 6: accidentally retraining the tokenizer
**What goes wrong:** Encoding with a freshly-trained tokenizer → different ids than the frozen artifact → invalidates the locked vocab and any future checkpoint.
**Avoid:** `from_json("artifacts/tokenizer.json")`, never `.train()`. (Carried Phase-2 Pitfall 6.) **Warning sign:** vocab_size ≠ 8192 or eos ≠ 8184.

## Code Examples

(See "Architecture Patterns" Pattern 1–4 above for the encode script, `get_batch_memmap`, the loop wiring, and best-val/sample hooks — all sourced from `github.com/karpathy/nanoGPT` and the existing codebase.)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Train the shipped checkpoint on Kaggle P100 (fp16 AMP) | Train locally on M3/MPS (fp32) | D-01 (2026-06-05) | Strengthens on-device/zero-budget thesis; no AMP, plain fp32; Kaggle is optional fallback. |
| Kaggle Dataset memmap pinning | Local-disk `train.bin`/`val.bin` (gitignored) | D-09 | No Kaggle Dataset step; simpler. |
| `preflight_p100` | `preflight_device` (CUDA-P100→MPS→CPU) | D-02 (landed) | MPS is a first-class long-run device. |

**Deprecated/outdated:** the `scripts/preflight_demo.py` Kaggle `DATA_DIR=/kaggle/input/...` mount convention is vestigial under D-01; the Phase-5 entry script preflights local paths.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The active venv's macOS torch wheel exposes a working MPS backend at training scale. | Standard Stack / M3 Reality | Long run can't use the GPU; falls back to CPU (slower but still works — D-01a accepts this). Mitigated by the preflight + smoke gate. |
| A2 | All model ops (Linear/Embedding/LayerNorm/softmax/gelu/cross_entropy/masked_fill) are MPS-covered; CPU fallbacks are rare. | M3 Reality / Pitfall 2 | Frequent silent fallbacks tank throughput. Mitigated by `PYTORCH_ENABLE_MPS_FALLBACK=1` + throughput probe. |
| A3 | Live TinyStoriesV2 file sizes (2.23 GB / 22.5 MB) and the HF resolve URLs. | Standard Stack | Wrong URL/size → download fails; caught immediately at download time. |
| A4 | PersonaCore (13.9M/384d, MPS) reaches a coherent-register val loss (~1.5–1.8, ppl ~5–6) in ≤ ~2 epochs. | Token Budget | If it needs far more tokens/time, D-04 "as long as it takes" + resumability absorb it; not fatal, just longer. |
| A5 | MPS RNG/determinism is weaker than CPU; cross-device bitwise reproduction not guaranteed. | M3 Reality | The CPU test suite remains the determinism oracle; the MPS run is validated by finite-loss + overfit smoke, not bitwise equality. |

**These five assumptions are the items discuss-phase/the planner should confirm or gate behind the calibration smoke before the long run.**

## Open Questions

1. **Exact LR / batch / grad_accum / max_steps for the long run** — deliberately UNRESOLVED; this is the calibration study's output (Open Q1). Recommendation: plan a calibration task that produces these numbers; do not hardcode.
2. **Real MPS tokens/sec at 13.9M/384d on this specific M3** — unmeasured (Open Q2). Recommendation: the Stage-1 throughput probe measures it; expected hundreds of ms/iter order-of-magnitude.
3. **Does `loop.py` need a periodic in-loop checkpoint, or is end-of-call enough?** — Current loop saves only at the end of `train()`. For multi-hour, kill-survivable runs, add a periodic `save_checkpoint(latest.pt)` every K steps. Recommendation: small additive change; flag for the planner.
4. **`estimate_loss` val source for the memmap path** — currently takes an in-RAM `val_ids`; the memmap path needs it to accept `val.bin` + use `get_batch_memmap`. Recommendation: localized change to `estimate_loss`.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `torch` + MPS backend | The MPS long run (PRE-02) | ✗ in research sandbox; ✓ expected in the project's 3.11 venv | `2.7.*` (per CLAUDE.md) | CPU fp32 run (slower; D-01a-accepted) |
| `numpy` | memmap build + sampling | ✓ (project dep) | 2.x | — |
| Frozen tokenizer | encode (PRE-01) | ✓ `artifacts/tokenizer.json` present (vocab 8192, eos 8184) | — | — |
| TinyStoriesV2 `.txt` files | corpus | ✗ not yet downloaded (`data/` empty) | — | re-download from HF resolve URLs |
| Disk for `.bin` (~1.1 GB) + raw (~2.25 GB) | corpus storage | assumed available | — | — |

**Missing with no fallback:** none blocking — `torch`/MPS is confirmed wired in code (D-02) and just needs the venv; the corpus is a one-time download.
**Missing with fallback:** the MPS run falls back to CPU fp32 if MPS misbehaves (D-01a explicitly accepts this).

**Note:** Research ran without an active venv (no `torch` importable here). The planner/executor MUST work inside the mandatory Python 3.11 venv; the preflight + finite-loss smoke is the gate that confirms MPS actually works before committing to the long run.

## Validation Architecture

> `nyquist_validation` is enabled (config.json `workflow.nyquist_validation: true`). This section seeds VALIDATION.md.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x (existing; CPU-only, GPU/MPS-free suite) |
| Config file | none dedicated; `tests/conftest.py` + fixtures present |
| Quick run command | `pytest tests/test_memmap_data.py -x` |
| Full suite command | `make test` (CPU-only, must stay green) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PRE-01 | Encode round-trips: decode(first N tokens of train.bin) matches `tok.encode(first raw doc)` | unit | `pytest tests/test_memmap_data.py::test_encode_roundtrip -x` | ❌ Wave 0 |
| PRE-01 | One EOS between docs: `count(==8184) ≈ num_docs`, no doubled/missing EOS | unit | `pytest tests/test_memmap_data.py::test_one_eos_between_docs -x` | ❌ Wave 0 |
| PRE-01 | `get_batch_memmap` in-bounds (x,y shapes; max index ≤ len-1; uint16→int64) | unit | `pytest tests/test_memmap_data.py::test_get_batch_memmap_inbounds -x` | ❌ Wave 0 |
| PRE-01 | No leakage: train.bin and val.bin built from disjoint files (official split) | unit | `pytest tests/test_memmap_data.py::test_no_leakage_disjoint -x` | ❌ Wave 0 |
| PRE-02 | Finite-loss MPS smoke: one forward/backward on MPS → `isfinite(loss)` | smoke (skipif no MPS) | `pytest tests/test_mps_smoke.py -x` | ❌ Wave 0 |
| PRE-02 | Overfit-one-batch on MPS drives loss → ~0 (reuse existing overfit pattern, device="mps") | smoke (skipif no MPS) | `pytest tests/test_mps_smoke.py::test_overfit_mps -x` | ❌ Wave 0 |
| PRE-02 | Resumability bit-for-bit across a simulated kill (memmap path) | unit (CPU) | `pytest tests/test_resume_memmap.py -x` | ❌ Wave 0 (extends `test_resume_curve.py`) |
| PRE-03 | Best-val-loss tracking: best.pt holds the run's lowest val loss; perplexity=exp(val_loss) recorded | unit (CPU) | `pytest tests/test_best_ckpt.py -x` | ❌ Wave 0 |
| PRE-02/03 | Acceptance evidence: curated coherent samples + recorded perplexity figure | manual (D-07) | manual review of best.pt samples + run.csv | manual-only (justified: human coherence judgement) |

### Sampling Rate
- **Per task commit:** `pytest tests/test_memmap_data.py -x` (quick).
- **Per wave merge:** `make test` (full CPU suite green).
- **Phase gate:** full CPU suite green + the MPS smoke passed on the real machine + the long run produced best.pt with a recorded perplexity and curated coherent samples, before `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `tests/test_memmap_data.py` — round-trip, one-EOS-between-docs, in-bounds get_batch, no-leakage (PRE-01). Needs a tiny committed multi-doc `.txt` fixture + a small built `.bin` (or build-in-test from the fixture).
- [ ] `tests/test_mps_smoke.py` — finite-loss + overfit on MPS, `@pytest.mark.skipif(not torch.backends.mps.is_available())` (PRE-02).
- [ ] `tests/test_resume_memmap.py` — extends `test_resume_curve.py` to the memmap data source (PRE-02 resumability).
- [ ] `tests/test_best_ckpt.py` — best-val-loss tracking + perplexity (PRE-03).
- [ ] Shared fixture: a small `tinystories_fixture.txt` (a few `<|endoftext|>`-separated micro-stories) for deterministic, GPU-free memmap tests.

*(The manual coherence/perplexity acceptance is human-judgement (D-07) and cannot be a unit test — it is a phase-gate manual check, justified.)*

## Project Constraints (from CLAUDE.md)

- **Zero budget / offline / on-device:** no paid compute/APIs; no wandb/online tooling; CSV+matplotlib logging only. Training now runs on the user's own M3.
- **From-scratch PyTorch only:** no HF transformers/PEFT model code; frozen from-scratch tokenizer reused (never `.train()`).
- **CPU-only test suite:** Phase-5 unit tests must stay GPU/MPS-free; the MPS run is exercised by a `skipif`-guarded smoke + manually.
- **Thin `scripts/` entry points, no CLI/argparse** (Phase-1 D-04): the encode and train entry scripts are thin; logic lives in the package.
- **`RuntimeConfig` is the single device/precision source of truth** — no scattered `torch.backends.mps` / `torch.cuda` checks in loop/data.
- **GSD workflow enforcement:** edits go through a GSD command; this is planned phase work via `/gsd:plan-phase` → `/gsd:execute-phase`.
- **MPS = fp32, no AMP/GradScaler/torch.compile** (D-02, verified in `config.py`).
- **bf16 guard unchanged** (Pascal-only error path retained).

## Security Domain

> `security_enforcement` is not set to a hard CSO regime here, but the relevant surface is small. This is an offline, single-user, local ML pretraining phase with no network services, no auth, no user input at runtime.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | minor | The only external input is the downloaded `.txt` corpus (trusted HF source) + the tokenizer file (own artifact). Assert tokenizer vocab/eos on load. |
| V6 Cryptography | no | No secrets, no crypto in this phase (Kaggle token unused under D-01). |
| Others (V2/V3/V4) | no | No auth/session/access-control surface — local offline training. |

### Known Threat Patterns
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Untrusted pickle on checkpoint load | Tampering / RCE | Resume uses `weights_only=False` on OWN trusted files only (already documented in `checkpoint.py`); never load a foreign checkpoint. Phase-8 slim ckpt uses `weights_only=True`. |
| Corrupt/incomplete corpus download | Tampering | Verify file sizes + a decode round-trip after download before encoding. |

## Sources

### Primary (HIGH confidence)
- Codebase: `src/personacore/{config.py, preflight.py, checkpoint.py, logging.py, training/loop.py, training/data.py, training/schedule.py, model/gpt.py}`, `tests/test_resume_curve.py`, `.gitignore`, `.planning/config.json` — read directly this session. Confirms D-02 landed + the exact reuse seams.
- `github.com/karpathy/nanoGPT` (train.py `get_batch`, data prepare) — the `np.uint16` `.bin` format + the "recreate np.memmap every batch to avoid a memory leak" pattern.

### Secondary (MEDIUM confidence)
- `arxiv.org/abs/2305.07759` (TinyStories paper) — small-model coherence, ~8.3M model GPT-4 grades ~8/10, 4×-size ≈ 50% loss / 80% ppl scaling.
- `medium.com/@kl.yap/replicating-tinystories-paper-38839d03ec81` — 8M GPT (8L/8H/128d, block 256, bs 12, lr 5e-4) → val loss ≈1.99, ~35k iters/~2 days on M1 CPU, ~600ms/iter, moderate coherence.
- `github.com/karpathy/nanoGPT` issue #28 + nanoGPT docs — MPS via `--device=mps`, ~2–3× faster than M1 CPU.
- `huggingface.co/datasets/roneneldan/TinyStories/tree/main` — TinyStoriesV2-GPT4 train (~2.23 GB) / valid (~22.5 MB) resolve URLs (sizes via CLAUDE.md; live fetch not confirmed in-session).

### Tertiary (LOW confidence)
- Throughput extrapolation from M1-CPU 8M numbers to M3-MPS 13.9M/384d — order-of-magnitude only; the calibration smoke is the real measurement.

## Metadata

**Confidence breakdown:**
- Reuse architecture / data path / resumability: HIGH — read the exact code; nanoGPT memmap pattern is canonical.
- D-02 verification: HIGH — confirmed in `config.py`/`preflight.py` + git log.
- Token budget / expected val loss / coherence bar: MEDIUM — external anchors, not this exact config.
- MPS throughput / op-coverage: MEDIUM — must be measured by the calibration smoke (deliberately not pre-decided).

**Research date:** 2026-06-05
**Valid until:** ~2026-07-05 (stable; the only fast-moving piece is torch MPS op-coverage, re-check at run time via the smoke gate)
