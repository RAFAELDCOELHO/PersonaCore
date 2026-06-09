# Phase 7: Evaluation - Pattern Map

**Mapped:** 2026-06-09
**Files analyzed:** 8 new/modified files
**Analogs found:** 8 / 8

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/personacore/evaluation/__init__.py` | package barrel | — | `src/personacore/generation/__init__.py` | exact |
| `src/personacore/evaluation/perplexity.py` | service (eval) | batch / transform | `src/personacore/training/loop.py::estimate_loss` + `training/data.py::get_batch_memmap` | role-match |
| `src/personacore/config.py` (EDIT) | config | — | `src/personacore/config.py::ModelConfig` (self — additive fields) | exact (in-place) |
| `src/personacore/model/gpt.py` (EDIT) | model | request-response | `src/personacore/model/gpt.py::GPT` (self — gate two seams) | exact (in-place) |
| `scripts/evaluate.py` | script (driver) | request-response | `scripts/pretrain_tinystories.py` | exact |
| `scripts/run_ablations.py` | script (driver) | batch | `scripts/pretrain_tinystories.py` + `training/loop.py::train` | role-match |
| `tests/test_perplexity.py` | test | — | `tests/test_generation.py` (tiny-CPU-fixture style) | role-match |
| `tests/test_ablation_config.py` | test | — | `tests/test_gpt_weight_tying.py` + `tests/test_gpt_param_count.py` | exact |
| `results/results.md` + `results/abl_*.csv` | artifact | file-I/O | `src/personacore/logging.py::CSVLogger` (CSV); committed markdown | role-match |

---

## Pattern Assignments

### `src/personacore/config.py` — EDIT (additive flags)

**Analog:** itself (`ModelConfig`, lines 76-92). This is an in-place additive edit.

**Current `ModelConfig` body** (`config.py:86-92`) — append the two new fields here, NOT reorder:
```python
vocab_size: int = 8192  # LOCKED by Phase 2 (was the Phase-1 placeholder).
eos_id: int = 8184  # shared atomic EOS id, recorded in checkpoint (D-03); top-pinned (D-03a).
block_size: int = 256
n_layer: int = 6
n_head: int = 6
n_embd: int = 384
dropout: float = 0.0
```

**Action — add two backward-compatible fields (defaults reproduce today's arch bit-for-bit):**
```python
weight_tying: bool = True   # False = untied lm_head (no-weight-tying ablation, EVAL-03)
use_pos_emb: bool = True     # False = drop learned positional embedding (no-pos ablation, EVAL-03)
```

**Critical:** `save_checkpoint` does `asdict(model_config)` (`checkpoint.py:65`) → future saves gain two keys. The existing `best.pt` dict has only 7 keys and is loaded by `model.load_state_dict` only (NOT rebuilt from the stored dict — `checkpoint.py:96`), so it stays loadable. `GPT(ModelConfig(**blob["model_config"]))` works whether or not the keys exist — missing keys fall back to the new `True`/`True` defaults.

---

### `src/personacore/model/gpt.py` — EDIT (gate two seams)

**Analog:** itself (`GPT.__init__` + `GPT.forward`). Two precise lines change; everything else is untouched.

**Seam 1 — weight tying (`gpt.py:174-177`, currently unconditional):**
```python
# (3) Weight tying AFTER init: share the SAME nn.Parameter so data_ptr() is identical
# (NOT a .data.clone()/copy_, which makes two tensors — RESEARCH Pitfall 2). The surviving
# tensor is the embedding init (std 0.02); lm_head is never separately re-initialized.
self.lm_head.weight = self.wte.weight
```
**Action — gate on the flag (default branch = today's behavior):**
```python
if config.weight_tying:
    self.lm_head.weight = self.wte.weight   # today's tied default
# else: lm_head.weight stays its own freshly-init'd tensor (untied; +vocab*n_embd params)
```

**Seam 2 — positional embedding add (`gpt.py:188-194`, currently unconditional):**
```python
def forward(self, idx, targets=None):
    B, T = idx.shape
    assert T <= self.config.block_size, f"seq len {T} > block_size {self.config.block_size}"
    tok_emb = self.wte(idx)  # (B, T, C)
    pos = torch.arange(T, device=idx.device)
    pos_emb = self.wpe(pos)  # (T, C) — broadcasts over batch.
    x = self.drop(tok_emb + pos_emb)
```
**Action — gate the positional add (default branch = today's behavior):**
```python
    tok_emb = self.wte(idx)  # (B, T, C)
    x = tok_emb
    if self.config.use_pos_emb:
        pos = torch.arange(T, device=idx.device)
        x = x + self.wpe(pos)
    x = self.drop(x)
```

**Constraint — these existing tests MUST stay green under the new defaults** (make "full suite green" an explicit phase gate):
- `tests/test_gpt_weight_tying.py::test_lm_head_shares_storage_with_token_embedding` — asserts `lm_head.weight.data_ptr() == wte.weight.data_ptr()` (depends on `weight_tying=True` default).
- `tests/test_gpt_param_count.py::test_param_count_in_target_band` — asserts `10M <= count <= 15M` with the tied default (~13.89M). `count_parameters` dedups by `data_ptr()`; untying inflates by `vocab*n_embd = 3,145,728`.
- `tests/test_gpt_init.py`, `tests/test_gpt_model.py`, `tests/test_gpt_overfit.py`, `tests/test_config.py`, `tests/test_checkpoint.py`, `tests/test_best_ckpt.py`.

**Rejected alternative (do NOT do):** subclassing `GPT` in the ablation script to override the tie/pos behavior. It duplicates the forward pass (drift risk) and the no-tie ablation is deliberately chosen to exercise the REAL Phase-4 weight-tying seam — a subclass tests a fork, not the seam.

---

### `src/personacore/evaluation/perplexity.py` — NEW (deterministic full-val sweep)

**Analog:** `training/loop.py::estimate_loss` (the eval posture) + `training/data.py::get_batch_memmap` (the memmap re-open idiom). A NEW function is required (D-02) — `estimate_loss` does 20 RANDOM batches (non-deterministic, mean-of-means), not a corpus PPL.

**`estimate_loss` posture to mirror** (`loop.py:70-102`) — `@torch.no_grad()`, `model.eval()`:
```python
@torch.no_grad()
def estimate_loss(model, val_ids, train_cfg, model_cfg, device, iters=20):
    rng = _rng_state()
    model.eval()
    ...
    _, loss = model(xb, yb)   # uses the forward (logits, loss) contract
    ...
    model.train()
    _restore_rng(rng)
    return sum(losses) / len(losses)
```

**Memmap re-open idiom to mirror** (`data.py:84` — re-open per use to avoid the nanoGPT RSS leak):
```python
data = np.memmap(bin_path, dtype=np.uint16, mode="r")
```

**`GPT.forward` CE contract** (`gpt.py:198-204`) — note it returns a **mean** loss (`reduction="mean"`); the sweep MUST recompute CE with `reduction="sum"`:
```python
logits = self.lm_head(x)  # (B, T, V)
if targets is None:
    return logits, None
B, T, V = logits.shape
loss = F.cross_entropy(logits.view(B * T, V), targets.view(B * T))  # MEAN — do not accumulate this
return logits, loss
```

**Action — new `perplexity()` (verified pattern from RESEARCH §Pattern 1):**
```python
import math
import numpy as np
import torch

@torch.no_grad()
def perplexity(model, val_bin_path, block_size, device, batch_size=32):
    """Deterministic full-val PPL over NON-OVERLAPPING block_size windows.
    Returns (ppl, total_tokens). PPL = exp(total_CE / total_tokens); total_tokens is the
    EXACT auditable denominator (D-03). A length-L window scores L-1 transitions (token 0
    is context-only). reduction='sum' is mandatory — never accumulate forward's mean loss.
    """
    model.eval()
    data = np.memmap(val_bin_path, dtype=np.uint16, mode="r")
    n = len(data)
    total_ce, total_tokens = 0.0, 0
    for i in range(0, n - 1, block_size):
        chunk = torch.from_numpy(data[i:min(i + block_size + 1, n)].astype(np.int64)).to(device)
        if chunk.numel() < 2:
            continue
        x = chunk[:-1].unsqueeze(0)
        y = chunk[1:].unsqueeze(0)
        logits, _ = model(x)
        ce = torch.nn.functional.cross_entropy(
            logits.view(-1, logits.size(-1)), y.view(-1), reduction="sum"
        )
        total_ce += ce.item()
        total_tokens += y.numel()
    return math.exp(total_ce / total_tokens), total_tokens
```

**Accounting invariants (test these):** denominator `= corpus_len - n_windows` (each window's first token is unpredictable); final single trailing token (`numel < 2`) is skipped; PPL is nearly block-size-invariant. `val.bin` is 12,636,923 tokens (verified).

---

### `src/personacore/evaluation/__init__.py` — NEW (barrel)

**Analog:** `src/personacore/generation/__init__.py` (re-export pattern):
```python
from .core import collect, generate
from .sampling import apply_temperature, next_token, top_k_filter, top_p_filter
from .text import generate_text, generate_text_str

__all__ = ["apply_temperature", "collect", "generate", ...]
```
**Action:** `from .perplexity import perplexity` + `__all__ = ["perplexity"]` (add a strided variant only if free — deferred).

---

### `scripts/evaluate.py` — NEW (headline PPL + curated samples driver)

**Analog:** `scripts/pretrain_tinystories.py` — thin no-argparse driver: `_REPO_ROOT`-relative path constants + a `main()`, logic in the package (Phase-1 D-04).

**`best.pt` load idiom to copy** (`pretrain_tinystories.py:117-121` — the trusted-file pattern):
```python
blob = torch.load(BEST_PATH, weights_only=False)  # own trusted file
model.load_state_dict(blob["model"])
model.to(runtime.device)
# blob["val_loss"] == 0.7378 (recorded 20-random-batch estimate; ppl 2.091) — NOT the headline
```
> Prefer reconstructing via the stored config (QA-02): `GPT(ModelConfig(**blob["model_config"]))` then `load_state_dict(blob["model"])`. The existing `best.pt` has 7 config keys → missing flag keys fall back to `True`/`True` defaults = the trained arch.

**MPS-fallback env set BEFORE `import torch`** (`pretrain_tinystories.py:32`) — mirror in any driver that runs on MPS:
```python
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
```

**Path-constant + preflight idiom** (`pretrain_tinystories.py:43-49, 65`):
```python
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
VAL_BIN = _REPO_ROOT / "data" / "val.bin"
TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"
summary = preflight_device(strict=True)
```

**Action — EVAL-01:** load `best.pt`, call `evaluation.perplexity(model, VAL_BIN, ModelConfig().block_size, runtime.device)`, print `ppl` AND `total_tokens` (D-03). **EVAL-02:** loop fixed prompts through `generation.generate_text_str` (see Shared Patterns).

---

### `scripts/run_ablations.py` — NEW (4-run cohort driver)

**Analog:** `scripts/pretrain_tinystories.py` (driver shell) + `training/loop.py::train` (the harness, reused verbatim).

**`train()` keyword-only signature to call** (`loop.py:150-174`) — pass an explicit pre-seeded `model` + matching `model_config`; only the model knob differs per run:
```python
train(
    train_config=cfg_reduced,      # SAME TrainConfig (lr/warmup/max_steps) for all 4 runs
    runtime_config=runtime,
    model=model,                    # explicit pre-built model (seed BEFORE building it)
    model_config=ModelConfig(**knob),
    train_bin=TRAIN_BIN, val_bin=VAL_BIN,
    eos_id=model_cfg.eos_id,
    log_path=f"results/abl_{name}.csv",
    best_checkpoint_path=f"checkpoints/abl_{name}.pt",
    eval_interval=EVAL_INTERVAL,
    checkpoint_interval=CHECKPOINT_INTERVAL,
)
```

**Fairness hygiene (RESEARCH Pitfall 3):** `train()` only seeds the default model when `model is None` (`loop.py:220-231`). Here we pass an explicit `model`, so the driver MUST call `seed_everything(seed)` (`seeding.py`) immediately before each `GPT(ModelConfig(**knob))` build, and reuse the SAME `TrainConfig` (LR/warmup/`max_steps`=reduced budget) and same `train_bin`/`val_bin` across all four runs. Note: a different `n_layer` consumes different init RNG draws → post-init streams diverge slightly (acceptable; data draws are what matter and are re-seeded).

**Cohort knobs (verified param counts):**
```python
KNOBS = {
    "baseline":  {},                       # 6/6/384 tied, pos-emb  -> 13,891,584 params
    "no_tie":    {"weight_tying": False},  # +3,145,728 (untied lm_head = vocab*n_embd) -> 17,037,312
    "no_pos":    {"use_pos_emb": False},   # -98,304 (dropped wpe = block_size*n_embd)  -> 13,793,280
    "depth_cut": {"n_layer": 3},           # -5,323,392 -> 8,568,192  (preferred over width: no head-div constraint)
}
```

**Calibration (D-07):** an early task runs a single short baseline (~5-10k steps) at the real `TrainConfig` LR, `EVAL_INTERVAL=250`, picks the smallest budget where samples read coherent AND the val-loss slope flattened (target val_loss ~1.0-1.3), then LOCKS `max_steps` for all four runs. Reuse the EVAL-01 `perplexity()` for each row's PPL column so the cohort is internally comparable.

**Per-run CSV:** `train()` already writes the curve via `CSVLogger` to `log_path` (`loop.py:296, 323`) — no new logging code. Header fields are `CSV_FIELDNAMES = ["step","train_loss","val_loss","lr","tokens","wall_clock"]` (`loop.py:45`).

---

### `tests/test_perplexity.py` — NEW (EVAL-01 accounting)

**Analog:** `tests/test_generation.py` — tiny CPU `GPT` fixture style (`block_size=8, vocab_size=16, n_layer=1, n_head=1, n_embd=8`), never `best.pt`/`val.bin` (keep CPU-fast). Build a hand-made ~300-token `np.uint16` fixture array on disk.

**Fixture-model idiom to copy** (`test_generation.py:31-46`):
```python
def _tiny_model():
    return GPT(ModelConfig(block_size=8, vocab_size=16, n_layer=1, n_head=1, n_embd=8, eos_id=15))
```

**Action — three cases (RESEARCH Test Map):** `test_matches_bruteforce` (PPL == a brute-force per-token reference on the fixture), `test_token_count` (denominator == `corpus_len - n_windows`), `test_partial_window` (final partial window scored, single trailing token skipped).

---

### `tests/test_ablation_config.py` — NEW (EVAL-03 flag semantics)

**Analog:** `tests/test_gpt_weight_tying.py` (`data_ptr()` identity) + `tests/test_gpt_param_count.py` (`count_parameters` dedup-by-`data_ptr`).

**`data_ptr` identity assert to copy** (`test_gpt_weight_tying.py:18-19`):
```python
model = GPT(ModelConfig())
assert model.lm_head.weight.data_ptr() == model.wte.weight.data_ptr()
```

**`count_parameters` helper to reuse** (`test_gpt_param_count.py:16-21`):
```python
def count_parameters(model) -> int:
    seen = {}
    for p in model.parameters():
        seen[p.data_ptr()] = p.numel()
    return sum(seen.values())
```

**Action — three cases:** `test_defaults_unchanged` (`GPT(ModelConfig())` → tied `data_ptr`, ~13.89M); `test_untie` (`weight_tying=False` → DISTINCT `data_ptr`, +3,145,728 params); `test_no_pos` (`use_pos_emb=False` → forward runs, no `wpe` contribution, −98,304 params).

---

### `results/results.md` + `results/abl_*.csv` — NEW (committed artifacts)

**Analog:** per-run CSVs come from `personacore.logging.CSVLogger` (already wired through `train()` — no new writer). The markdown table is a new committed artifact (stdlib write, no pickle — matches the JSON-only artifact discipline).

**`CSVLogger` contract** (`logging.py:16-38`) — append-mode, header-once, restart-safe; `.log(**row)` flushes:
```python
class CSVLogger:
    def __init__(self, path, fieldnames): ...   # header only if file new/empty
    def log(self, **row) -> None: ...           # append + flush
```

**Action — git-tracking gotcha (RESEARCH Open Q3):** `logs/` and `checkpoints/` and `*.pt` are **gitignored** (verified `.gitignore`). The committed cohort CSVs + results table MUST live under a TRACKED path — use `results/` (NOT `logs/`). Verify `results/` is not ignored before committing.

**Results table columns (D-08):** *variant name · param count · held-out perplexity (reduced budget) · best val-loss · one-line "what this shows"*.

---

## Shared Patterns

### Curated qualitative samples (EVAL-02) — reuse the locked Phase-6 path
**Source:** `src/personacore/generation/text.py::generate_text_str` (`text.py:96-102`), re-exported from `generation/__init__.py`.
**Apply to:** `scripts/evaluate.py`.
```python
from personacore.tokenizer import from_json
from personacore.generation import generate_text_str

tok = from_json("artifacts/tokenizer.json")     # FROZEN — never retrain
PROMPTS = ["Once upon a time", "The little robot", "", ...]  # planner picks the fixed set
for p in PROMPTS:
    greedy = generate_text_str(model, tok, p, max_new_tokens=200, greedy=True)
    warm   = generate_text_str(model, tok, p, max_new_tokens=200, temperature=0.8, top_p=0.95)
```
`generate_text` prepends `[eos_id]` (empty prompt → exactly `[eos_id]`, the trained document-start seed — `text.py:72`), strips the prompt (D-02), stops on EOS without emitting it (D-05), and `model.config.eos_id` is read, never hardcoded (`text.py:65`). Present samples as REPRESENTATIVE with an honest selection note (portfolio integrity). Do NOT use `generate()` for perplexity.

### Checkpoint load (trusted-file)
**Source:** `scripts/pretrain_tinystories.py:117-121` / `checkpoint.py::load_checkpoint`.
**Apply to:** `scripts/evaluate.py`, `scripts/run_ablations.py` (re-loading each `abl_*.pt` to score it).
- `torch.load(path, weights_only=False)` is for OWN trusted files only — never a foreign checkpoint.
- Config travels with weights: `GPT(ModelConfig(**blob["model_config"]))`.

### Seeding (fresh-run hygiene)
**Source:** `src/personacore/seeding.py::seed_everything` (`seeding.py:34`).
**Apply to:** every fresh ablation run and the calibration smoke.
- Call ONCE before building each variant's model; on resume do NOT call it (`load_checkpoint` restores RNG state instead). `RuntimeConfig()` auto-disables AMP on MPS/CPU (`config.py:55-59`) — ablation runs inherit fp32 for free.

### Thin no-argparse driver shell
**Source:** `scripts/pretrain_tinystories.py` (whole file).
**Apply to:** both new scripts. `_REPO_ROOT`-relative path constants, a `main()`, `if __name__ == "__main__": main()`, `preflight_device(strict=True)` gate, `PYTORCH_ENABLE_MPS_FALLBACK=1` set before `import torch`. No argparse (Phase-1 D-04).

---

## No Analog Found

None. Every file has a close in-repo analog — Phase 7 is ~90% wiring of existing seams. The only genuinely new logic is the perplexity accounting (small but bug-prone — the `-1`/`reduction="sum"` denominator details) and the two additive `ModelConfig` flags + their two `if` branches.

---

## Metadata

**Analog search scope:** `src/personacore/{model,training,generation,evaluation}`, `src/personacore/{config,checkpoint,logging,seeding}.py`, `scripts/`, `tests/`, `.gitignore`.
**Files scanned:** 13 source/test files read in full or targeted.
**Pattern extraction date:** 2026-06-09
**Verified facts carried from RESEARCH:** baseline 13,891,584 params; no_tie +3,145,728; no_pos −98,304; 3-layer 8,568,192; `val.bin` 12,636,923 tokens; `best.pt` step 49000 val_loss 0.7378 (ppl 2.091, a random-batch estimate — NOT the headline).
