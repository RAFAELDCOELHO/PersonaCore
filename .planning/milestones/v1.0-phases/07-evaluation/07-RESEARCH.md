# Phase 7: Evaluation - Research

**Researched:** 2026-06-09
**Domain:** LM evaluation — held-out perplexity accounting, qualitative sampling, architecture ablation methodology (from-scratch PyTorch GPT, ~13.9M params, M3/MPS fp32)
**Confidence:** HIGH (the entire surface is in-repo code already inspected; no external library uncertainty)

## Summary

Phase 7 is a **measurement + small-training** phase over an already-trained from-scratch GPT. Almost
everything it needs already exists in `src/personacore/`: the `forward(idx, targets=...) -> (logits, loss)`
contract for CE, `get_batch_memmap`/`np.memmap` over `data/val.bin`, `load_checkpoint`/`best.pt`,
the `generate()`/`generate_text()` stack for qualitative samples, the `train()` harness for the
ablation cohort, the `CSVLogger` for per-run curves, and open-dict checkpoints that carry config.
The three deliverables (EVAL-01 deterministic full-val perplexity; EVAL-02 curated samples;
EVAL-03 ablation trio + table) map almost 1:1 onto existing seams.

**The one genuine tension the planner must resolve up front:** the CONTEXT says this phase "does
**not** change the model," but two of the three locked ablations (no-weight-tying, no-positional-
embeddings) **cannot be expressed today** — `gpt.py` hard-wires `self.lm_head.weight = self.wte.weight`
(line 177) and unconditionally adds `pos_emb` (lines 192–194), and `ModelConfig` has **no**
`weight_tying` or `use_pos_emb` flag. The depth/width cut, by contrast, works **immediately** via
existing `ModelConfig(n_layer=...)`/`n_embd` fields. So two of three ablations require a small,
*additive, backward-compatible* edit to `config.py` + `gpt.py` (new flags defaulting to the current
behavior). This does not change the trained `best.pt`'s architecture or invalidate any checkpoint —
but it **is** a model-code edit, and the plan must say so explicitly rather than pretend otherwise.

**Primary recommendation:** Add two backward-compatible `ModelConfig` flags (`weight_tying: bool = True`,
`use_pos_emb: bool = True`) gated inside `GPT.__init__`/`forward` so the default reproduces today's
architecture bit-for-bit (and every existing test still passes); build a new `evaluation/` module with
a deterministic non-overlapping-window `perplexity()` (using `forward` directly, NOT `estimate_loss`,
NOT `generate`); reuse `train()` + `CSVLogger` + open-dict checkpoints for a 4-run ablation cohort
(fresh baseline + 3 variants) at a calibration-chosen reduced budget; emit a committed markdown table
+ per-run CSVs.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Deterministic full-val perplexity (EVAL-01) | Model / eval module | Data (memmap) | CE comes from `GPT.forward(targets=)`; tokens come from the `val.bin` memmap; new tiling logic owns the accounting |
| Curated qualitative samples (EVAL-02) | Generation (`generate_text`) | Tokenizer | Reuses the locked Phase-6 `generate()`/text-wrapper path verbatim; no new decoding |
| Ablation variant construction (EVAL-03) | Model config + model | — | New backward-compatible `ModelConfig` flags + gated `GPT` branches express the three knobs |
| Ablation training cohort (EVAL-03) | Training (`train()`) | Logging / checkpoint | Reuses the proven loop; only `ModelConfig`/`TrainConfig` knobs + budget differ per run |
| Per-run curves + results table | Logging (`CSVLogger`) + a new driver script | — | CSV appender already exists; the table is a new committed artifact (markdown) |

## Standard Stack

This phase adds **no new third-party dependencies.** Everything is the already-pinned stack.

### Core (already installed, verified in-venv)
| Library | Version (verified) | Purpose | Why Standard |
|---------|--------------------|---------|--------------|
| `torch` | 2.7.1 (in `.venv`, MPS available) | `forward` CE, `no_grad`, tensor ops, checkpoint load | The whole model + harness; nothing new |
| `numpy` | 2.x (existing) | `np.memmap` tiling of `val.bin` | The existing `get_batch_memmap` data path uses it |
| `pytest` | ~=9.0 (existing `[dev]`) | EVAL unit tests | Repo test framework; CPU-only suite |

**Installation:** None. `pip install -e ".[cpu,dev]"` is already the established env (Python 3.11 venv,
verified `python 3.11.15`, `torch 2.7.1`, `mps True`).

**Version verification:** Ran `python -c "import torch; print(torch.__version__)"` inside `.venv` →
`2.7.1`, `torch.backends.mps.is_available() == True`. No registry install needed; no slopcheck needed.

## Package Legitimacy Audit

> Not applicable — this phase installs **zero** external packages. All code reuses the existing
> `personacore` package and its already-pinned, already-audited dependencies (`torch`, `numpy`,
> `pytest`). No registry fetch, no `npm`/`pip install` of a new name, no slopcheck surface.

## Project Constraints (from CLAUDE.md)

The planner MUST honor these (same authority as locked decisions):
- **Zero budget / on-device:** ablation cohort runs locally on M3/MPS, fp32. ~4× the calibration budget
  (baseline + 3 variants) must stay within "a few hours on M3" (CONTEXT D-07). No paid compute, no APIs.
- **fp32 on M3/MPS, no AMP, no `GradScaler`, no `torch.compile`:** `RuntimeConfig` auto-disables AMP on
  MPS (verified `config.py:56–59`); the ablation runs inherit this for free by reusing `train()`.
- **From-scratch ethos / no HuggingFace model code:** perplexity uses `GPT.forward` + `F.cross_entropy`
  (a primitive, already in the model). No `evaluate`/`lm-eval-harness`/HF metrics libraries.
- **No CLI/argparse; thin `scripts/` entry points** (Phase-1 D-04): the eval driver follows
  `pretrain_tinystories.py`'s pattern — constants + a `main()`, logic in the package.
- **Offline CSV logging only** (no wandb): reuse `personacore.logging.CSVLogger`.
- **GSD workflow enforcement:** all edits go through a GSD command (this is plan-phase research, fine).
- **Reproducibility (QA-02):** open-dict checkpoints carry config + RNG + git SHA; each ablation run is
  reproducible and its config travels with its checkpoint. `seed_everything` before each fresh run.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EVAL-01 | Perplexity computed on a held-out set | New `evaluation.perplexity()` tiles `data/val.bin` (12,636,923 tokens, verified) in non-overlapping `block_size=256` windows, sums CE over `GPT.forward(idx, targets=)`, returns `exp(total_CE/total_tokens)` + the token count. Loads the real `best.pt` (step 49000, recorded `val_loss=0.7378`) via `load_checkpoint`. |
| EVAL-02 | Curated qualitative generation samples captured | Reuse `generation.generate_text` / `generate_text_str` (Phase-6 locked path, `[eos_id]`-seeded) over a fixed story-starter prompt set; greedy + a small temp/top-p spread; presented as representative with an honest selection note. |
| EVAL-03 | 2–3 architecture ablations + comparison table | New backward-compatible `ModelConfig` flags (`weight_tying`, `use_pos_emb`) + existing `n_layer`/`n_embd` express the trio; reuse `train()` for the 4-run cohort at a calibrated reduced budget; reuse the EVAL-01 `perplexity()` for the cohort's PPL column; emit a committed markdown table + per-run CSVs via `CSVLogger`. |

## Architecture Patterns

### System Architecture Diagram

```
                         ┌─────────────────────────────────────────────┐
EVAL-01 (headline PPL)   │  checkpoints/best.pt (step 49000)            │
                         │     │ load_checkpoint (open-dict, config)    │
                         │     ▼                                        │
   data/val.bin ────────►│  evaluation.perplexity(model, val_bin):     │
   (12,636,923 uint16)   │     tile NON-OVERLAPPING block_size windows  │
                         │     for each window: logits,loss=forward(    │
                         │        x[:-1] -> predict x[1:], targets)     │
                         │     total_CE += loss_sum ; total_tok += T    │
                         │     return exp(total_CE/total_tok), total_tok│──► headline PPL + token count
                         └─────────────────────────────────────────────┘

                         ┌─────────────────────────────────────────────┐
EVAL-02 (samples)        │  best.pt model  +  artifacts/tokenizer.json  │
   fixed prompt set ────►│  generation.generate_text(model, tok, p, …)  │──► curated samples (md)
                         │     [eos_id]-seed, greedy + temp/top-p spread │
                         └─────────────────────────────────────────────┘

                         ┌─────────────────────────────────────────────┐
EVAL-03 (ablations)      │  calibration: short run → pick reduced budget│
   shared seed/data/LR ─►│  for variant in {baseline, no_tie, no_pos,   │
                         │                   depth_cut}:                 │
                         │     model = GPT(ModelConfig(**knob))          │
                         │     train(reduced budget, same seed/data/LR)  │──► per-variant best.pt
                         │     ppl = evaluation.perplexity(model,val_bin)│──► per-run CSV
                         │  assemble row: name·params·PPL·val_loss·note  │──► committed results table (md)
                         └─────────────────────────────────────────────┘
```

### Recommended Project Structure
```
src/personacore/
├── evaluation/              # NEW package (mirrors generation/ layering)
│   ├── __init__.py          # re-export perplexity (+ maybe a strided variant if free)
│   └── perplexity.py        # deterministic non-overlapping full-val sweep
├── config.py                # EDIT: add weight_tying=True, use_pos_emb=True (backward-compatible)
└── model/gpt.py             # EDIT: gate weight-tie + pos-emb on the new flags (default = today)
scripts/
├── evaluate.py              # NEW thin driver: headline PPL + curated samples (no argparse)
└── run_ablations.py         # NEW thin driver: calibration + 4-run cohort + results table
tests/
├── test_perplexity.py       # NEW: window accounting, known-CE oracle, denominator audit
└── test_ablation_config.py  # NEW: flags default to today's arch; data_ptr untie; no-pos forward
results/ (or docs/)          # NEW committed artifacts: results.md table + per-run CSVs
```

### Pattern 1: Deterministic non-overlapping perplexity (EVAL-01, D-01..D-03)
**What:** Tile the whole `val.bin` into back-to-back `block_size`-token windows, sum CE over every
predicted token, divide by the exact total predicted-token count, exponentiate.
**When to use:** The single canonical headline number (and each ablation cohort row).
**Why a new function, not `estimate_loss`:** `estimate_loss` (`loop.py:70`) does 20 **random** batches
and returns a **mean of per-batch means** — non-deterministic and not a true corpus PPL. D-02 requires
its own deterministic full-sweep.

```python
# Source: derived from gpt.py forward contract + get_batch_memmap (data.py) — in-repo, verified
import math
import numpy as np
import torch

@torch.no_grad()
def perplexity(model, val_bin_path, block_size, device, batch_size=32):
    """Deterministic full-val perplexity over NON-OVERLAPPING block_size windows.

    Returns (ppl, total_tokens). total_tokens is the EXACT denominator so the number is auditable
    (D-03). Every predicted token counts, including inter-document eos (the model was trained that
    way). PPL = exp(total_CE / total_tokens).
    """
    model.eval()
    data = np.memmap(val_bin_path, dtype=np.uint16, mode="r")
    n = len(data)
    total_ce = 0.0
    total_tokens = 0
    # A window of length L predicts L-1 targets (token 0 has no prior context to be predicted from).
    # Use stride = block_size so windows are non-overlapping; the model sees block_size tokens and
    # scores the block_size-1 next-token transitions inside it.
    step = block_size
    starts = range(0, n - 1, step)  # need at least one (x, y) pair: i and i+1 must exist
    for i in starts:
        end = min(i + block_size + 1, n)        # +1 so x and the shifted y both fit
        chunk = torch.from_numpy(data[i:end].astype(np.int64)).to(device)
        if chunk.numel() < 2:
            continue                            # final dangling token: nothing to predict
        x = chunk[:-1].unsqueeze(0)             # (1, T)
        y = chunk[1:].unsqueeze(0)              # (1, T)
        logits, _ = model(x)                    # ignore the mean loss; recompute a SUM
        ce = torch.nn.functional.cross_entropy(
            logits.view(-1, logits.size(-1)), y.view(-1), reduction="sum"
        )
        total_ce += ce.item()
        total_tokens += y.numel()
    return math.exp(total_ce / total_tokens), total_tokens
```

**Critical accounting answers (research Q1):**
- **Does the model predict token 0?** No. In next-token LMs, position 0 has no predecessor to predict
  it; a length-`L` window scores `L-1` transitions. So a `block_size=256` window contributes **255**
  predicted tokens, not 256. Be explicit about this in the writeup.
- **Final partial window:** the loop above naturally handles it — the last chunk may be `< block_size+1`
  long; it still scores `len(chunk)-1` transitions. A single trailing token (`numel < 2`) is skipped
  (nothing to predict). **No tokens are silently dropped except that final unpredictable one.**
- **Exact denominator:** `total_tokens = Σ (len(window) - 1)`. For 12,636,923 val tokens tiled at
  stride 256 with the per-window `-1`, the denominator is **`12,636,923 - (number_of_windows)`**
  (each window loses its first token as unpredictable). Report `total_tokens` alongside PPL (D-03) so a
  reviewer can audit `exp(total_CE/total_tokens)`.
- **`reduction="sum"` is mandatory.** `GPT.forward(targets=)` returns a **mean** CE (`F.cross_entropy`
  default, `gpt.py:203`). Averaging per-window means would mis-weight a short final window. Call
  `forward(x)` to get logits, then recompute CE with `reduction="sum"` (shown above). Do NOT use the
  loss the model returns for the accumulation.

### Pattern 2: Backward-compatible ablation flags (EVAL-03, research Q2 — the load-bearing one)
**What:** Add `weight_tying: bool = True` and `use_pos_emb: bool = True` to `ModelConfig`; gate the two
hard-wired behaviors in `GPT` on them. Defaults reproduce today's architecture exactly.
**Why required:** Verified by reading the source — there is **no existing toggle**:
- `gpt.py:177` → `self.lm_head.weight = self.wte.weight` is unconditional.
- `gpt.py:192–194` → `pos = arange(T); pos_emb = self.wpe(pos); x = drop(tok_emb + pos_emb)` is
  unconditional.
- `config.py` `ModelConfig` has fields `vocab_size, eos_id, block_size, n_layer, n_head, n_embd,
  dropout` — and **nothing** for tying or positional embeddings.

```python
# config.py — additive, backward-compatible (new fields default to current behavior)
weight_tying: bool = True   # False = untied lm_head (the no-weight-tying ablation)
use_pos_emb: bool = True    # False = drop learned positional embedding (the no-pos ablation)

# gpt.py __init__ — gate the tie
if config.weight_tying:
    self.lm_head.weight = self.wte.weight     # today's behavior (default)
# else: leave lm_head.weight as its own freshly-init'd tensor (untied)

# gpt.py forward — gate the positional add
x = tok_emb
if self.config.use_pos_emb:
    pos = torch.arange(T, device=idx.device)
    x = x + self.wpe(pos)
x = self.drop(x)
```

**Reconciliation with "does not change the model" (research Q2):** This **is** a model-code edit, and
the plan must own that contradiction honestly rather than route around it. The mitigations that keep it
safe:
1. **Defaults are bit-for-bit identical to today.** `GPT(ModelConfig())` produces the exact same
   architecture, the same ~13.9M params, the same tied `data_ptr()`. The existing
   `test_gpt_weight_tying`, `test_gpt_param_count`, `test_gpt_init`, etc. must all still pass — make
   "existing model tests stay green" an explicit task gate.
2. **`best.pt` is untouched and still loads.** `asdict(model_config)` in the checkpoint will simply
   gain two keys on *future* saves; loading the existing `best.pt` reconstructs `GPT(ModelConfig())`
   with the new defaults → identical model. (If `load_checkpoint` ever reconstructs `ModelConfig` from
   the stored dict, the old dict lacks the two keys — verify the load path uses `**stored` into the
   dataclass; missing keys fall back to defaults, which is correct. The current `load_checkpoint` only
   `model.load_state_dict(ckpt["model"])` and does NOT rebuild ModelConfig, so this is a non-issue for
   `best.pt`.)
3. **Per-CONTEXT framing:** the phase "does not change the trained model, tokenizer, training loop,
   checkpoint format, or `generate()`." Adding two optional `ModelConfig` flags + two `if` branches
   changes none of those *artifacts* — `best.pt`, `tokenizer.json`, `loop.py`, the checkpoint schema,
   and `generate()` are all untouched. It changes `model/gpt.py` and `config.py` **additively**. The
   honest planner note: "EVAL-03 requires two additive, default-preserving model-config flags; this is
   the minimum edit that lets the locked no-tie / no-pos ablations exist at all."

**Alternative considered (and why rejected):** subclass `GPT` in the ablation script to override the
tie/pos behavior without touching `gpt.py`. Rejected because (a) it duplicates the forward pass (drift
risk vs the real model — the exact pitfall the from-scratch tests guard against), and (b) the
no-weight-tying ablation is *deliberately* chosen (CONTEXT "Specific Ideas") to exercise the real
Phase-4 weight-tying seam verified by the `data_ptr()` identity test — a subclass would test a fork,
not the seam. The additive flag keeps one model, one seam, one set of tests.

### Pattern 3: Ablation cohort via the existing `train()` (EVAL-03, D-06..D-08)
**What:** A driver that, for each of `{baseline, no_tie, no_pos, depth_cut}`, builds
`GPT(ModelConfig(**knob))` and calls the **untouched** `train()` with **identical** `seed`, data
(`train_bin`/`val_bin`), LR schedule (same `TrainConfig` LR/warmup), and step budget — only the model
knob differs. Each run writes its own `latest.pt`/`best.pt` and its own `CSVLogger` curve, then
`perplexity()` scores it.
**When to use:** The fair-comparison cohort (NOT compared to the 50k `best.pt` — D-06).

```python
# Source: pretrain_tinystories.py pattern + train() signature (loop.py:150) — in-repo
KNOBS = {
    "baseline":   {},                        # 6/6/384, tied, pos-emb  -> ~13.89M params
    "no_tie":     {"weight_tying": False},   # +3,145,728 params (verified: vocab*n_embd)
    "no_pos":     {"use_pos_emb": False},    # -98,304 params (verified: block_size*n_embd)
    "depth_cut":  {"n_layer": 3},            # ~8.57M params (verified)
}
for name, knob in KNOBS.items():
    seed_everything(seed)                    # SAME seed every run (fair-comparison hygiene)
    model = GPT(ModelConfig(**knob))
    train(train_config=cfg_reduced, model=model, model_config=ModelConfig(**knob),
          train_bin=TRAIN_BIN, val_bin=VAL_BIN,
          best_checkpoint_path=f"checkpoints/abl_{name}.pt",
          log_path=f"results/abl_{name}.csv", ...)
    model.load_state_dict(torch.load(f"checkpoints/abl_{name}.pt", weights_only=False)["model"])
    ppl, ntok = perplexity(model, VAL_BIN, ModelConfig().block_size, runtime.device)
```

**Verified param counts (computed in-venv this session):**
| Variant | Knob | Params | Δ vs baseline |
|---------|------|--------|---------------|
| baseline | — | **13,891,584** | — |
| no_tie | `weight_tying=False` | 17,037,312 | +3,145,728 (untied lm_head = vocab×n_embd) |
| no_pos | `use_pos_emb=False` | 13,793,280 | −98,304 (dropped wpe = block_size×n_embd) |
| depth_cut (6→3 layers) | `n_layer=3` | **8,568,192** | −5,323,392 |

### Anti-Patterns to Avoid
- **Using `estimate_loss` for the headline PPL.** It's 20 random batches → non-deterministic, not a
  corpus number. The recorded `best.pt val_loss=0.7378` (ppl 2.091) is *that* random-batch estimate;
  EVAL-01's deterministic full sweep will produce a **slightly different, canonical** number — expect
  it near but not equal to 2.091, and present it as the authoritative one.
- **Calling `generate()` for perplexity.** PPL needs teacher-forced CE from `forward(targets=)`, not
  autoregressive sampling (CONTEXT explicit; Phase-6 note: "perplexity uses `forward` directly").
- **Averaging per-window mean losses.** Mis-weights the short final window. Sum CE with
  `reduction="sum"`, divide by exact token count.
- **Comparing reduced-budget ablations to the 50k `best.pt`.** Different budgets = unfair (D-06). The
  ablation table is its own self-consistent cohort with a fresh reduced-budget baseline.
- **Cherry-picking EVAL-02 samples.** CONTEXT requires representative selection with an honest method
  note (portfolio integrity for a rigor audience).
- **Forking the model into a subclass for ablations.** Drifts from the tested real model; defeats the
  point of exercising the real weight-tying seam.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Memmap window iteration | A new file reader | `np.memmap(..., mode="r")` (as in `get_batch_memmap`) | Already the proven pattern; re-open per use to avoid the nanoGPT RSS leak |
| CE computation | A manual log-softmax + gather | `F.cross_entropy(..., reduction="sum")` over `forward` logits | Already a sanctioned primitive in the model; numerically stable |
| Checkpoint load | Manual `torch.load` + key plucking | `checkpoint.load_checkpoint` / the `best.pt` `["model"]` pluck (as `pretrain_tinystories.py:117`) | Open-dict format, `weights_only=False` for the trusted file, restores config |
| Qualitative sampling | A new decode loop | `generation.generate_text` / `generate_text_str` | Locked Phase-6 path; `[eos_id]`-seed, EOS-stop, no mojibake, prompt-strip |
| Per-run curve logging | A bespoke CSV writer | `personacore.logging.CSVLogger` | Restart-safe, header-once; the established offline-logging contract |
| Ablation training | A second training loop | `training.train(...)` with different `ModelConfig`/budget | The whole point of the harness; zero new training code |
| LR schedule for ablations | A new scheduler | `build_scheduler` via `TrainConfig` (reused by `train()`) | Identical schedule = fair comparison |

**Key insight:** Phase 7 is ~90% wiring of existing seams. The only genuinely new code is the
perplexity accounting (small, but the accounting details are where bugs hide) and the two additive
model-config flags. Everything else is reuse.

## Runtime State Inventory

> This is an additive measurement phase (new modules + two backward-compatible flag fields), not a
> rename/refactor. Included for the flag edit's blast radius.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `checkpoints/best.pt` (step 49000, val_loss 0.7378), `checkpoints/latest.pt`, `data/val.bin` (12,636,923 tokens), `logs/run.csv` (201 rows) | **Read-only.** `best.pt` reconstructs fine under new `ModelConfig` defaults (load path does NOT rebuild `ModelConfig` from the stored dict — it only `load_state_dict`s, verified `checkpoint.py:96`). New ablation checkpoints are NEW files. |
| Live service config | None — no external services, no DB, no daemon. Fully local. | None — verified by repo structure (no service config anywhere). |
| OS-registered state | None — no scheduled tasks, no pm2/systemd. | None — verified: only thin `scripts/` entry points, run by hand. |
| Secrets/env vars | `PYTORCH_ENABLE_MPS_FALLBACK=1` set in `pretrain_tinystories.py:32` for long MPS runs; ablation driver should set the same. No secrets. | Ablation/eval drivers that train on MPS should `os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK","1")` before `import torch` (mirror the pretrain script). |
| Build artifacts | None affected — pure-Python package, editable install; no compiled artifacts, no egg-info staleness from these edits. | None. |

**Test blast radius of the two new `ModelConfig` flags (must stay green):**
`test_config.py`, `test_gpt_weight_tying.py` (data_ptr identity — depends on default `weight_tying=True`),
`test_gpt_param_count.py` (13.9M band — depends on tied default), `test_gpt_init.py`,
`test_gpt_model.py`, `test_gpt_overfit.py`, `test_best_ckpt.py`, `test_checkpoint.py` (asdict round-trip
gains two keys — verify it tolerates extra keys; `asdict` always serializes all dataclass fields, so the
checkpoint just gets two more — harmless). Make "full existing suite green" a phase gate.

## Common Pitfalls

### Pitfall 1: The "+1" off-by-one in window tiling (the denominator bug)
**What goes wrong:** Slicing `data[i:i+block_size]` and treating it as both x and y, or forgetting that a
window of length L predicts only L-1 tokens — yields a wrong denominator and a subtly wrong PPL.
**Why it happens:** next-token shift is `x = chunk[:-1]`, `y = chunk[1:]`; the first token of each window
is context-only, never a prediction.
**How to avoid:** Read `end = min(i+block_size+1, n)` (the `+1` so the shifted y fits), score
`len(chunk)-1` transitions, accumulate `total_tokens += y.numel()`. Unit-test the denominator against a
hand-counted tiny array.
**Warning signs:** PPL differs from a brute-force per-token reference on a 300-token fixture; total_tokens
isn't `corpus_len - n_windows`.

### Pitfall 2: Mean-loss accumulation instead of summed CE
**What goes wrong:** Using the `loss` returned by `forward(targets=)` (a per-window **mean**) and
averaging across windows over-weights the short final window.
**Why it happens:** `gpt.py:203` uses `F.cross_entropy` default `reduction="mean"`.
**How to avoid:** Ignore the returned loss; recompute `F.cross_entropy(logits, y, reduction="sum")` and
divide once by the grand total. (Equivalently, weight each window's mean by its token count.)
**Warning signs:** PPL changes when you change `block_size` even though the data is identical (a correct
non-overlapping full sweep is nearly block-size-invariant; only the per-window first-token loss and the
final partial window cause tiny differences).

### Pitfall 3: Ablation unfairness via drifting RNG / data / schedule
**What goes wrong:** Variants train on different random batches, different init seeds, or a schedule that
implicitly differs (e.g. different `max_steps` changes the cosine curve), making deltas meaningless.
**Why it happens:** `train()` seeds the *default* model from `train_config.seed` only when `model is None`
(`loop.py:229`); here we pass an explicit `model`, so **we** must `seed_everything(seed)` before building
each variant's model AND the schedule shape depends on `TrainConfig.max_steps`/`warmup_steps`.
**How to avoid:** `seed_everything(seed)` immediately before each `GPT(...)` construction; use the SAME
`TrainConfig` (same LR, warmup, max_steps=reduced budget) for all four runs; same `train_bin`/`val_bin`.
The data sampler (`get_batch_memmap`) draws from global numpy RNG seeded identically → identical batch
sequence across variants. Note: a different `n_layer` consumes a different number of init RNG draws, so
**post-init** the RNG streams diverge slightly between variants — acceptable (data draws are what matter
and those are re-seeded), but document it. For maximum rigor, seed the data sampler independently of model
init if it falls out cheaply (not required).
**Warning signs:** Re-running the cohort gives different table numbers; the baseline's curve differs from
run to run.

### Pitfall 4: Reduced budget too short → ablation deltas are noise (research Q3)
**What goes wrong:** At a too-small step budget the baseline hasn't separated from the variants; all four
PPLs cluster and the "what this shows" story collapses.
**Why it happens:** Early training is dominated by easy n-gram statistics; architectural effects (esp.
positional embeddings, depth) show up only after the easy gains saturate.
**How to avoid (calibration methodology, D-07):** Run a single short baseline (~5–10k steps) at the real
`TrainConfig` LR, logging val-loss every ~250 steps (matching `EVAL_INTERVAL` in the pretrain script).
Pick the smallest budget where (a) periodic samples read as clearly coherent TinyStories-register text
(the same qualitative bar as Phase 5 D-07), and (b) the val-loss curve's slope has flattened to a small
fraction of its early slope (e.g. last-1k-step improvement < ~10–20% of first-1k-step improvement). The
full 50k run reached val_loss ~0.74; a reduced budget targeting val_loss in the ~1.0–1.3 range is
typically enough to separate these three ablations while staying a few hours total on M3. Lock the chosen
budget as `max_steps` for all four runs.
**Warning signs:** no_pos ≈ baseline (pos-emb effect needs more steps to matter at block_size 256), or
depth_cut ≈ baseline (both still underfit).

### Pitfall 5: Headline PPL ≠ the recorded 2.091
**What goes wrong:** Reviewers (or the writeup) expect EVAL-01 to reproduce `best.pt`'s recorded
`ppl 2.091`, but the deterministic full sweep gives a different number.
**Why it happens:** 2.091 = `exp(0.7378)` where 0.7378 is the **20-random-batch** `estimate_loss` at the
best step — not a full-corpus deterministic PPL. They are different estimators of the same quantity.
**How to avoid:** Present EVAL-01's full-sweep number as the canonical one, and (optionally) note the
random-batch estimate as the in-training signal it was. Report the token count so the new number is
auditable (D-03).
**Warning signs:** A "bug hunt" triggered by a small discrepancy that is actually expected estimator
variance.

## Code Examples

### Loading `best.pt` for evaluation (the trusted-file pattern)
```python
# Source: scripts/pretrain_tinystories.py:117-121 (in-repo, verified)
import torch
from personacore.config import ModelConfig
from personacore.model import GPT

blob = torch.load("checkpoints/best.pt", weights_only=False)  # own trusted file
model = GPT(ModelConfig(**blob["model_config"]))  # config travels with weights (QA-02)
model.load_state_dict(blob["model"])
model.eval()
# blob["val_loss"] == 0.7378 (recorded random-batch estimate, step 49000)
```
> Note: `blob["model_config"]` currently has 7 keys; after adding the two flags, *future* saves carry 9.
> The **existing** `best.pt` dict has 7 keys, so `ModelConfig(**blob["model_config"])` works whether or
> not the flags exist — missing keys fall back to the new `True`/`True` defaults (reproducing the trained
> architecture exactly). Verify this construction in a test against the real `best.pt`.

### Curated qualitative samples (EVAL-02, reusing the locked path)
```python
# Source: generation/text.py generate_text_str + pretrain_tinystories.py sample loop — in-repo
from personacore.tokenizer import from_json
from personacore.generation import generate_text_str

tok = from_json("artifacts/tokenizer.json")  # frozen, never retrain
PROMPTS = ["Once upon a time", "The little robot", "", ...]  # planner picks the fixed set
for p in PROMPTS:
    greedy = generate_text_str(model, tok, p, max_new_tokens=200, greedy=True)
    warm   = generate_text_str(model, tok, p, max_new_tokens=200, temperature=0.8, top_p=0.95)
    # capture both; present representative (not cherry-picked) with an honest selection note
```
> The empty prompt seeds exactly `[eos_id]` (free-running story) — the same seed the training sample
> hook used (D-03), so it matches the trained document-start register.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Random-batch val-loss as "the" PPL | Deterministic full-corpus non-overlapping sweep | This phase (D-01) | One canonical, auditable, reproducible headline number |
| Single model, no ablations | Architecture ablation cohort with a fresh fair baseline | This phase (EVAL-03) | The differentiator that lifts the project above a clone |

**Deprecated/outdated for this phase:**
- Strided/sliding-window (GPT-2-style) perplexity: a more rigorous, lower number, but more compute.
  **Confirmed deferred** by CONTEXT (D-01 locks non-overlapping; deferred ideas list it). Research Q5
  answer: **stay a footnote.** It does NOT fall out cheaply — it requires re-running `forward` at every
  offset (≈`block_size`× the compute of the non-overlapping sweep over a 12.6M-token corpus on CPU/MPS)
  and would only lower the number, not change the ablation story. Note it as a writeup footnote
  ("non-overlapping windows slightly *over*-estimate PPL vs a strided sweep, because early-in-window
  tokens have less context"); do not implement unless trivially free.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | A reduced budget reaching val_loss ~1.0–1.3 separates the three ablations within "a few hours on M3" | Pitfall 4 / calibration | If wrong, calibration (D-07) corrects it empirically — that's exactly what the calibration step is for. Low risk: the methodology, not the number, is what's locked. |
| A2 | `no_pos` (drop positional embeddings) trains stably at this scale (it will be far worse, but finite-loss) | Pattern 3 / table | If it diverges, that *is* a valid ablation finding ("positional info is load-bearing"); the table's "what this shows" still holds. Low risk. |
| A3 | The existing model-test suite stays green with `weight_tying=True`/`use_pos_emb=True` defaults | Runtime State Inventory | Verified by reasoning (defaults reproduce today's arch); planner must make "suite green" an explicit gate to confirm empirically. Low risk. |
| A4 | `asdict(ModelConfig)` tolerating two extra keys won't break `test_checkpoint`/`test_best_ckpt` | Runtime State Inventory | `asdict` serializes all fields; load path doesn't rebuild ModelConfig from the dict for `best.pt`. Verify in the test gate. Low-medium risk. |

**These four are empirical and resolved by the phase's own calibration + test gates — none require user
confirmation before planning. No locked decision rests on an unverified external fact.**

## Open Questions (RESOLVED)

1. **Exact reduced step budget** — **RESOLVED:** calibrated empirically in Plan 07-03 (D-07). The
   `calibrate()` step in `scripts/run_ablations.py` measures the smallest `max_steps` where the
   fresh baseline reads coherent AND the val-loss slope has flattened, then locks it as
   `REDUCED_MAX_STEPS` for the cohort. The executor records the calibrated value in 07-03-SUMMARY.
   - What we know: full run = 50k steps → val_loss ~0.74; eval cadence 250; samples coherent by the end.
   - Resolution: the methodology (calibration), not a hard-coded number, is what's locked — mirrors
     the Phase-5 calibration-smoke pattern.

2. **Depth-vs-width for the third ablation (D-05 lets the planner pick).** — **RESOLVED:** the third
   ablation is **`n_layer=6→3`** (`depth_cut`, 8,568,192 params verified). Chosen over narrowing
   `n_embd` — a clean ~38% param cut, no head-divisibility constraint (`n_embd % n_head == 0`,
   `gpt.py:64`), and "depth matters" is the cleaner one-line story.

3. **Where the committed results artifacts live** (`results/` vs `docs/`). — **RESOLVED:** the
   tracked **`results/`** dir (table `results.md` + per-run `abl_*.csv` + `samples.md`), consumed by
   Phase-8 `demo.ipynb`. Verified NOT in `.gitignore` (unlike `logs/` and `checkpoints/`, which are
   ignored); Plans 07-02 and 07-03 write to `results/` and confirm git-tracking before committing.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11 venv | All phase work | ✓ | 3.11.15 (`.venv`) | — (CI also pins 3.11) |
| torch | CE, training, load | ✓ | 2.7.1 | — |
| MPS backend | Ablation training (fast) | ✓ | `mps True` | CPU fp32 (slower but correct; tests are CPU-only anyway) |
| `data/val.bin` | EVAL-01 | ✓ | 12,636,923 tokens (25,273,846 bytes) | — |
| `data/train.bin` | EVAL-03 cohort training | ✓ | 2.5 GB memmap | — |
| `checkpoints/best.pt` | EVAL-01 headline, EVAL-02 | ✓ | step 49000, val_loss 0.7378 | — |
| `artifacts/tokenizer.json` | EVAL-02 decode | ✓ | frozen 8192-vocab | — |
| `logs/run.csv` | reference curve | ✓ | 201 rows (250→50000) | — |

**Missing dependencies with no fallback:** None. Every input the phase consumes already exists on disk
(verified by `ls`). This phase can be planned and executed entirely offline on the current M3.

## Validation Architecture

> `.planning/config.json` not inspected for `nyquist_validation`; the repo has a first-class pytest
> suite (35 test files, CPU-only), so validation infra exists. Including this section.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest ~=9.0 (`[dev]` extra), verified installed |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths=["tests"]`, `pythonpath=["."]`) |
| Quick run command | `pytest tests/test_perplexity.py -x -q` |
| Full suite command | `make test` (= `pytest -q`) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EVAL-01 | Non-overlapping PPL math matches a brute-force per-token reference on a tiny fixture | unit | `pytest tests/test_perplexity.py::test_matches_bruteforce -x` | ❌ Wave 0 |
| EVAL-01 | Denominator equals `corpus_len - n_windows` (auditable token count) | unit | `pytest tests/test_perplexity.py::test_token_count -x` | ❌ Wave 0 |
| EVAL-01 | Final partial window handled; single trailing token skipped | unit | `pytest tests/test_perplexity.py::test_partial_window -x` | ❌ Wave 0 |
| EVAL-03 | `weight_tying=True`/`use_pos_emb=True` defaults reproduce today's arch (data_ptr tied, params 13.89M) | unit | `pytest tests/test_ablation_config.py::test_defaults_unchanged -x` | ❌ Wave 0 |
| EVAL-03 | `weight_tying=False` → untied lm_head (distinct data_ptr, +3.15M params) | unit | `pytest tests/test_ablation_config.py::test_untie -x` | ❌ Wave 0 |
| EVAL-03 | `use_pos_emb=False` → forward runs, no `wpe` contribution, −98,304 params | unit | `pytest tests/test_ablation_config.py::test_no_pos -x` | ❌ Wave 0 |
| EVAL-03 | Existing model suite stays green under new defaults | regression | `pytest tests/test_gpt_weight_tying.py tests/test_gpt_param_count.py tests/test_gpt_init.py -x` | ✅ exists |
| EVAL-02 | Samples are deterministic under greedy + fixed seed (smoke, tiny model) | unit | `pytest tests/test_generation.py -x` (existing covers greedy determinism) | ✅ exists |

### Sampling Rate
- **Per task commit:** `pytest tests/test_perplexity.py tests/test_ablation_config.py -x -q`
- **Per wave merge:** `make test` (full CPU suite — guards the model-flag blast radius)
- **Phase gate:** Full suite green before `/gsd:verify-work`; the real cohort + headline PPL are
  produced by the (non-pytest) driver scripts run by hand on M3.

### Wave 0 Gaps
- [ ] `tests/test_perplexity.py` — covers EVAL-01 (brute-force oracle, token-count audit, partial window).
      Use a tiny CPU model + a hand-built ~300-token array fixture (NOT `best.pt`/`val.bin` — keep CPU-fast).
- [ ] `tests/test_ablation_config.py` — covers EVAL-03 flag semantics (defaults unchanged; untie; no-pos).
- [ ] No framework install needed (pytest present).

## Security Domain

> `security_enforcement` not found in init context; this is a local, offline, no-network, no-input
> measurement phase (no auth, no sessions, no external input, no untrusted data). Minimal surface.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth surface (local script) |
| V3 Session Management | no | No sessions |
| V4 Access Control | no | No access control surface |
| V5 Input Validation | minimal | EVAL-02 prompts are a fixed in-repo set, not user input. `generate_text` already enforces a `max_new_tokens` DoS cap (`text.py:67`). |
| V6 Cryptography | no | None |

### Known Threat Patterns for this stack
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Untrusted checkpoint deserialization | Tampering | `best.pt` loads `weights_only=False` but is the project's OWN trusted file (`checkpoint.py` docstring). Ablation checkpoints are also own-generated. No external checkpoint is loaded. Keep this invariant: never `weights_only=False` on a foreign file. |
| Pickle in results artifacts | Tampering | Results table is markdown; per-run logs are CSV (stdlib `csv`). No pickle in shippable artifacts — matches the tokenizer-artifact discipline (JSON data-only). |

## Sources

### Primary (HIGH confidence — in-repo, read this session)
- `src/personacore/model/gpt.py` — forward contract, hard-wired weight-tie (L177) + pos-emb (L192–194), no flags
- `src/personacore/config.py` — `ModelConfig` fields (no tying/pos flags); `RuntimeConfig` MPS→fp32/AMP-off (L56–59)
- `src/personacore/training/loop.py` — `train()` signature, `estimate_loss` (20 random batches), `sample`
- `src/personacore/training/data.py` — `get_batch_memmap` (`np.memmap`, re-open-per-call), nanoGPT indexing
- `src/personacore/checkpoint.py` — open-dict `save`/`load`, `weights_only=False`, config travels with weights
- `src/personacore/generation/{core,text}.py` — `generate`/`generate_text` (EVAL-02 path), `[eos_id]`-seed
- `src/personacore/logging.py` — restart-safe `CSVLogger`
- `scripts/pretrain_tinystories.py` — the thin-driver pattern + `best.pt` load + perplexity print idiom
- `tests/test_gpt_param_count.py`, `tests/conftest.py` — `data_ptr` dedup count, test fixtures
- **In-venv measurements:** `torch 2.7.1` / `mps True`; baseline 13,891,584 params; no_tie +3,145,728;
  no_pos −98,304; 3-layer 8,568,192; `best.pt` step 49000 val_loss 0.7378 (ppl 2.091); `val.bin`
  12,636,923 tokens; `run.csv` 201 rows
- CONTEXT D-01..D-08, upstream 05/06 CONTEXT, REQUIREMENTS EVAL-01..03, ROADMAP §Phase 7

### Secondary (MEDIUM)
- CLAUDE.md technology-stack prescription (fp32/MPS, no AMP, from-scratch ethos, offline CSV)

### Tertiary (LOW)
- None — no WebSearch/Context7 needed; the entire surface is in-repo code.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new deps; versions verified in-venv.
- Architecture (PPL accounting, ablation flags): HIGH — derived directly from inspected source; param
  deltas computed empirically this session.
- Pitfalls: HIGH (accounting, fairness, estimator-variance) / MEDIUM (exact reduced budget — delegated to
  calibration by design).

**Research date:** 2026-06-09
**Valid until:** 2026-07-09 (stable — pure in-repo code; only the empirical reduced-budget number is
intentionally left to calibration).
