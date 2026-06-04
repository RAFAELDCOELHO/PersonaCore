# Architecture Research

**Domain:** From-scratch small GPT-style language model (PyTorch), dual-environment (Kaggle GPU train / laptop CPU infer)
**Researched:** 2026-06-04
**Confidence:** HIGH (nanoGPT structure, torch.amp device-agnostic API, LoRA module-injection, EWC Fisher pattern all verified against current docs and reference implementations)

## Executive Summary

This is a well-trodden architecture — a nanoGPT-style decoder-only transformer — but with three project-specific constraints that shape the layout: (1) everything is from-scratch and unit-tested per component, so module boundaries must be clean enough to test in isolation; (2) one codebase must train on a Kaggle P100 and run inference on a laptop CPU, so device/AMP concerns must be centralized, not scattered; (3) Milestone 2 will add from-scratch LoRA (adapters wrapping `nn.Linear`) and EWC (continual-learning regularizer hooking the training loop). M1 must leave clean seams for both **without building them now**.

The recommended structure is a `src/personacore/` package split into `tokenizer/`, `model/`, `data/`, `training/`, `generation/`, and `config/`, plus thin entry-point `scripts/` and `notebooks/` that wire components together for Kaggle vs. laptop. The single most important architectural decision for forward-compatibility is to **build the GPT decoder out of a small set of named, swappable submodules** (especially the linear projections in attention and the MLP) so that M2's LoRA injector can find and wrap them by name, and to **structure the training step as a function that computes a base loss plus a pluggable list of extra loss terms**, so EWC's Fisher-weighted penalty drops in as one more term without rewriting the loop.

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                         ENTRY POINTS (thin)                            │
│   scripts/train.py      scripts/sample.py      notebooks/demo.ipynb    │
│   app/demo_gradio.py    scripts/train_tokenizer.py                     │
│        │                     │                      │                  │
├────────┴─────────────────────┴──────────────────────┴─────────────────┤
│                      CONFIG LAYER (dataclasses)                         │
│   ModelConfig   TrainConfig   DataConfig   GenConfig   RuntimeConfig    │
│   (RuntimeConfig owns device + AMP resolution — single source)         │
├────────────────────────────────────────────────────────────────────────┤
│                          CORE PACKAGE (src/personacore/)               │
│  ┌────────────┐  ┌──────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ tokenizer/ │  │  data/   │  │     model/       │  │ generation/  │  │
│  │ BPE train/ │→ │ Dataset, │→ │ GPT decoder      │→ │ sampler:     │  │
│  │ encode/dec │  │ batching │  │ (blocks/attn/mlp)│  │ temp, top-k  │  │
│  └────────────┘  └──────────┘  │ + bigram baseline│  └──────────────┘  │
│        │              │        └──────────────────┘         ▲          │
│        │              │                 ▲                    │          │
│        │              └─────────────────┤                    │          │
│        │                       ┌────────┴─────────┐          │          │
│        │                       │    training/     │──────────┘          │
│        │                       │ loop, optimizer, │                     │
│        │                       │ checkpoint, AMP, │                     │
│        │                       │ loss assembly    │  ◄── EWC hook (M2)  │
│        │                       └──────────────────┘                     │
├────────┴─────────────────────────────────────────────────────────────┤
│                          ARTIFACTS (on disk)                           │
│   tokenizer.json   checkpoints/*.pt (model+opt+config+step)   logs/    │
└────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| `tokenizer/` | Train BPE on corpus; `encode(str)->ids`, `decode(ids)->str`; serialize vocab+merges to disk | From-scratch BPE (merge-rank dict + regex pre-tokenizer); no HF |
| `data/` | Turn token-id stream into batched `(x, y)` next-token tensors; train/val split | `np.memmap` over a flat `.bin` of token ids + random-offset batch sampler (nanoGPT pattern) |
| `model/` | Define network forward passes and parameter init; `bigram.py` baseline + `gpt.py` decoder built from `attention.py`, `mlp.py`, `block.py`, `embeddings.py` | Pure `nn.Module` subclasses; named submodules; no training/device logic inside |
| `training/` | Own the training step, optimizer, LR schedule, AMP, gradient clipping, checkpoint save/resume, eval/loss logging | `train()` loop + `loss_fn` assembly + `checkpoint.py`; **the one place AMP and the loss-term list live** |
| `generation/` | Autoregressive decode: feed prompt, sample next token (temperature, top-k), append, repeat to length/EOS | Stateless `generate(model, ids, cfg)` function |
| `config/` | Typed configuration objects; resolve device and AMP dtype from environment | `@dataclass` configs; optional YAML load/override |
| `scripts/` + `app/` + `notebooks/` | Wire components for a specific environment (Kaggle train vs. laptop demo); no business logic | Thin orchestration only |

**Boundary rule:** `model/` never imports `training/` and never references device or AMP. The model is a pure function of (params, input). Everything stateful and environment-dependent lives in `training/` + `config/`. This is what makes per-component unit tests trivial and what keeps the M2 extension points clean.

## Recommended Project Structure

```
PersonaCore/
├── src/
│   └── personacore/
│       ├── __init__.py
│       ├── config/
│       │   ├── __init__.py
│       │   ├── configs.py          # ModelConfig, TrainConfig, DataConfig, GenConfig dataclasses
│       │   └── runtime.py          # RuntimeConfig: resolve_device(), amp_dtype(), autocast ctx
│       ├── tokenizer/
│       │   ├── __init__.py
│       │   ├── bpe.py              # train(), encode(), decode(), save(), load()
│       │   └── pretokenize.py      # regex split / byte handling
│       ├── data/
│       │   ├── __init__.py
│       │   ├── prepare.py          # text -> token ids -> flat .bin (memmap)
│       │   └── loader.py           # get_batch(split) -> (x, y) on device
│       ├── model/
│       │   ├── __init__.py
│       │   ├── bigram.py           # baseline LM (build/test first)
│       │   ├── embeddings.py       # token + positional embeddings
│       │   ├── attention.py        # causal multi-head self-attention
│       │   ├── mlp.py              # position-wise feed-forward
│       │   ├── block.py            # transformer block (attn + mlp + norm + residual)
│       │   └── gpt.py              # GPT: stacks blocks, lm_head, forward()/loss
│       ├── training/
│       │   ├── __init__.py
│       │   ├── loop.py             # train(): step loop, eval, logging, AMP, clip
│       │   ├── optim.py            # optimizer + LR schedule (warmup+cosine)
│       │   ├── losses.py           # assemble_loss(): base CE + [extra terms]  ◄ EWC seam
│       │   └── checkpoint.py       # save/load {model, optimizer, config, step, rng}
│       ├── generation/
│       │   ├── __init__.py
│       │   └── sampler.py          # generate(model, ids, gen_cfg)
│       └── adapters/               # ◄── M2 ONLY. Empty placeholder package in M1 (see note)
│           └── __init__.py
├── scripts/
│   ├── train_tokenizer.py          # CLI: corpus -> tokenizer.json
│   ├── prepare_data.py             # CLI: TinyStories -> train.bin / val.bin
│   ├── train.py                    # CLI: config -> trained checkpoint (Kaggle entry)
│   └── sample.py                   # CLI: checkpoint + prompt -> text (laptop entry)
├── app/
│   └── demo_gradio.py              # local on-device chat UI
├── notebooks/
│   ├── kaggle_train.ipynb          # imports src/, runs training on P100
│   └── demo.ipynb                  # training curves, sampling — research artifact
├── configs/
│   ├── model_15m.yaml              # ~10–15M param decoder hyperparams
│   ├── train_tinystories.yaml      # batch/lr/steps for Kaggle P100
│   └── train_cpu_smoke.yaml        # tiny config for laptop sanity tests
├── tests/
│   ├── test_bpe.py                 # roundtrip encode/decode, merge correctness
│   ├── test_data.py                # batch shapes, no train/val leakage
│   ├── test_attention.py           # causal mask (no future leakage), shapes
│   ├── test_gpt.py                 # forward shape, loss decreases on overfit-1-batch
│   ├── test_bigram.py
│   ├── test_sampler.py             # determinism w/ fixed seed, top-k/temp behavior
│   └── test_checkpoint.py          # save->load->identical params
├── checkpoints/                    # gitignored artifacts
├── data/                           # gitignored .bin files
├── requirements.txt
├── pyproject.toml                  # installable package (pip install -e .)
└── CLAUDE.md
```

### Structure Rationale

- **`src/personacore/` as an installable package (`pip install -e .`):** This is the single most important portability decision. A Kaggle notebook, a local Gradio app, and `pytest` all do `from personacore.model.gpt import GPT` — identical import path everywhere. Avoids the classic Kaggle pain of `sys.path` hacks and relative-import breakage. The package is the contract; notebooks/scripts are disposable wiring.
- **`model/` split into one file per concept:** attention/mlp/block/gpt as separate modules is not over-engineering here — it directly serves the "per-component unit test" portfolio requirement. A reviewer can open `attention.py` and `test_attention.py` side by side. It also gives LoRA (M2) clean, named targets to wrap.
- **`config/` separates pure hyperparameters from runtime resolution:** `configs.py` holds *what the model is* (deterministic, serialized into checkpoints). `runtime.py` holds *where it runs* (device, AMP) — resolved fresh per environment, never serialized. Keeping these apart is why the same checkpoint loads identically on P100 and CPU.
- **`scripts/` thin and CLI-shaped, `notebooks/` thin and import-only:** Kaggle runs notebooks; a notebook should be ~20 lines that import `personacore` and call `train(cfg)`. Logic in notebooks is untestable and unreviewable — keep it out.
- **`adapters/` exists as an empty package in M1:** Reserving the namespace (not the implementation) signals intent in the repo without scope-creeping. Zero code, just `__init__.py`. (Optional — see Extension Points; if you prefer no empty dirs, omit it and add in M2.)
- **Separate `configs/*.yaml` per environment:** `train_tinystories.yaml` (full P100 run) vs. `train_cpu_smoke.yaml` (10-step laptop sanity check) means the laptop can validate the *whole pipeline end-to-end* in seconds without a GPU. Critical for fast iteration when you can't always reach Kaggle.

## Architectural Patterns

### Pattern 1: Centralized Device + AMP Resolution (RuntimeConfig)

**What:** A single `RuntimeConfig` object resolves `device` ("cuda"/"cpu"), AMP `enabled`, and `amp_dtype` once at startup. Every device-dependent call (`.to(device)`, autocast, GradScaler) reads from it. Nothing else in the codebase calls `torch.cuda.is_available()`.

**When to use:** Always, given the dual-environment requirement. This is the linchpin of "one codebase, two environments."

**Trade-offs:** Tiny indirection cost; massive payoff in not hunting down scattered `.cuda()` calls when the laptop run breaks.

**Example:**
```python
@dataclass
class RuntimeConfig:
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    amp: bool = True            # auto-disabled on CPU below
    amp_dtype: str = "float16"  # P100 has no bf16; fp16+GradScaler on CUDA

    def __post_init__(self):
        if self.device == "cpu":
            self.amp = False    # CPU path: full fp32, no scaler — simplest correct default

    def autocast(self):
        # torch.amp device-agnostic API (verified current, PyTorch 2.x)
        return torch.autocast(device_type=self.device.split(":")[0],
                              dtype=getattr(torch, self.amp_dtype),
                              enabled=self.amp)

# training step:
scaler = torch.amp.GradScaler(device="cuda", enabled=rt.amp)  # no-op when disabled
with rt.autocast():
    logits, loss = model(x, y)
scaler.scale(loss).backward()
scaler.step(optimizer); scaler.update()
```
> Verified: `torch.autocast(device_type=...)` and `torch.amp.GradScaler(...)` are the current device-agnostic AMP API; `GradScaler(enabled=False)` is a clean no-op so the *same* loop runs on CPU. P100 (Pascal) has weak fp16 throughput and no bf16 — fp16 AMP gives modest gains; defaulting CPU to fp32 avoids the slow/buggy CPU-fp16 path entirely.

### Pattern 2: Pure Model, Stateful Trainer

**What:** `nn.Module`s in `model/` know only how to compute forward + loss. They take tensors, return tensors. All training state (optimizer, step count, AMP, checkpoints, device placement) lives in `training/`. The model's `forward(idx, targets=None)` returns `(logits, loss)` — loss optional so the same forward serves training and generation.

**When to use:** Always. This is the boundary that makes both unit testing and M2 extension clean.

**Trade-offs:** None meaningful at this scale. It's the nanoGPT convention for good reason.

**Example:**
```python
class GPT(nn.Module):
    def forward(self, idx, targets=None):
        x = self.embeddings(idx)
        for block in self.blocks:
            x = block(x)
        logits = self.lm_head(self.ln_f(x))
        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.flatten(0, 1), targets.flatten())
        return logits, loss
```

### Pattern 3: Loss Assembly with Pluggable Extra Terms (the EWC seam)

**What:** The training step never inlines `F.cross_entropy` directly. Instead it calls `assemble_loss(model, batch, extra_penalties=[])` which computes the base cross-entropy and adds each penalty term from a list. In M1 the list is empty. In M2, EWC appends one penalty.

**When to use:** Adopt the indirection in M1 (it costs ~5 lines), so M2's continual-learning regularizer is additive, not surgical.

**Trade-offs:** Slight over-abstraction for M1's empty list — but this is *exactly* the seam that prevents M2 from rewriting the training loop. Deliberate, documented, cheap.

**Example:**
```python
def assemble_loss(model, x, y, extra_penalties=()):
    _, base = model(x, y)
    total = base
    for penalty in extra_penalties:   # M1: empty. M2: [ewc_penalty]
        total = total + penalty(model)
    return total, base   # return base separately for clean logging
```

### Pattern 4: Self-Describing Checkpoints

**What:** A checkpoint is a dict bundling `{model_state, optimizer_state, model_config, step, val_loss, rng_state}` — not just `model.state_dict()`. The config travels *with* the weights, so loading on the laptop reconstructs the exact architecture with no out-of-band config.

**When to use:** Always. Essential for Kaggle→laptop transfer and for 30h/week-aware resumability.

**Trade-offs:** Slightly larger files (optimizer state ~2x model size) — negligible at 15M params (~60MB checkpoint), and droppable for inference-only "release" checkpoints.

**Example:**
```python
torch.save({"model": model.state_dict(), "optimizer": opt.state_dict(),
            "model_config": asdict(model_cfg), "step": step,
            "val_loss": val_loss, "rng": torch.get_rng_state()}, path)
# load on laptop CPU:
ckpt = torch.load(path, map_location="cpu")
model = GPT(ModelConfig(**ckpt["model_config"])); model.load_state_dict(ckpt["model"])
```

## Data Flow

### End-to-End Pipeline (offline-train → on-device-infer)

```
TRAINING (Kaggle P100, notebook):
  TinyStories raw text
      ↓  tokenizer.train()                    [one-time, scripts/train_tokenizer.py]
  tokenizer.json (vocab + merges)
      ↓  data/prepare.py: encode whole corpus → flat uint16 array
  train.bin / val.bin (np.memmap)
      ↓  data/loader.get_batch() → random offsets → (x, y) tensors → .to(device)
  batch (x, y)
      ↓  training/loop.py: autocast → model(x,y) → assemble_loss → scaler.backward → step
  gradient update  ──(every N steps)──► checkpoints/ckpt.pt  ──(resume)──┐
      └──────────────────── loop until step budget / 30h ────────────────┘

TRANSFER:
  checkpoints/ckpt.pt + tokenizer.json  ──download──►  laptop

INFERENCE (laptop CPU):
  prompt string
      ↓  tokenizer.encode()
  prompt ids
      ↓  generation/sampler.generate(model, ids, gen_cfg): loop {forward → top-k/temp sample → append}
  generated ids
      ↓  tokenizer.decode()
  output text  ──►  app/demo_gradio.py  |  notebooks/demo.ipynb
```

### Key Data Flows

1. **Tokenizer is built once, consumed everywhere:** `tokenizer.json` is an artifact produced before training and loaded identically at train time (to make `.bin`) and inference time (to encode prompts/decode output). The same vocab must be used end-to-end — a mismatch silently corrupts generation. Treat it as a frozen artifact post-training.
2. **Token ids never leave disk as text during training:** Corpus is encoded once into a memmapped `.bin`; the loader reads random windows. This decouples (slow, one-time) tokenization from (fast, repeated) batch fetching — the nanoGPT pattern, ideal under Kaggle time limits.
3. **Config flows into the checkpoint, not around it:** Model hyperparameters are serialized inside the checkpoint, so the laptop reconstructs the architecture from the file alone.
4. **Loss flows through an assembly point, not inline:** Every backward pass goes through `assemble_loss`. In M1 that is just cross-entropy; the indirection is the EWC seam.

## Suggested Build Order

Dependency-ordered so each component is testable the moment it's built, and each unblocks the next. This maps directly to phase structure.

```
1. config/        → dataclasses + RuntimeConfig (device/AMP). Foundational; everything imports it.
2. tokenizer/     → BPE train/encode/decode + tests (roundtrip). Independent of model.
   └─ parallelizable with model skeleton, but data/ needs it.
3. model/bigram   → baseline LM + test. Validates the model→loss→logits contract cheaply.
4. data/          → prepare.py + loader (needs tokenizer). Test batch shapes / no leakage.
5. training/loop  → minimal loop that overfits bigram on one batch (sanity: loss→0).
                    Establishes checkpoint + AMP + assemble_loss seams NOW (with empty term list).
6. model/ (GPT)   → embeddings → attention → mlp → block → gpt. Test each (causal mask!).
                    Swap GPT into the existing loop — loop already works, just a bigger model.
7. generation/    → sampler + tests (seeded determinism, top-k). Needs a trained-ish model.
8. Pretraining    → run full TinyStories on Kaggle; iterate to coherent generation.
9. demo           → Gradio app + demo.ipynb wiring (pure composition, no new core logic).
```

**Critical ordering insight:** Build the **training loop against the bigram baseline (step 5) before the full GPT (step 6)**. The loop, checkpointing, AMP toggle, and `assemble_loss` seam are all validated against a trivial model that overfits in seconds on a CPU. By the time the real transformer arrives, the entire training/checkpoint/device machinery is already proven — the only new risk is the model math itself, which `test_attention.py` (causal mask) and "overfit one batch" isolate. This de-risks the from-scratch foundation exactly as the two-milestone strategy intends.

## Extension Points for Milestone 2 (DESIGN FOR — DO NOT BUILD NOW)

These are seams to *leave open* in M1, each costing 0–5 lines. **No LoRA or EWC code ships in M1.** The goal is that M2 is additive, never a refactor.

### Seam A — LoRA adapter injection point (wraps `nn.Linear`)

**Where:** The linear projections inside `model/attention.py` (q/k/v/output projections) and `model/mlp.py`.

**What M1 must do (cheap):**
- Use **plain `nn.Linear`** for every projection (not fused custom linear ops, not functional `F.linear` with raw weight tensors). LoRA's standard injector walks the module tree and replaces `nn.Linear` instances by name — fused/functional layers have nothing to wrap. *(Verified: the standard from-scratch LoRA pattern is a recursive injector that finds `nn.Linear` submodules by name-match and swaps in a wrapper that freezes the base weight and adds a low-rank `B@A` path.)*
- Give submodules **stable, descriptive names** (e.g. `self.attn_qkv`, `self.attn_proj`, `self.mlp_fc`, `self.mlp_proj`) so M2 can target them by name pattern.
- Keep `forward` going through `self.linear(x)` (a module call), **not** through a captured weight tensor — so a wrapper substituted at that attribute is transparently used.

**What M2 will add (do NOT build now):** A `adapters/lora.py` with a `LoRALinear` wrapper (frozen base `nn.Linear` + trainable low-rank `A`, `B`) and an `inject_lora(model, target_names, rank)` function that swaps matching modules. Because the model already calls modules by attribute, injection is transparent — no change to `gpt.py`.

**M1 acceptance for this seam:** every adaptable matmul is a named `nn.Linear`. That's it. Do not add rank params, do not add a wrapper, do not freeze anything.

### Seam B — EWC training-loop hook (Fisher-weighted penalty)

**Where:** `training/losses.py::assemble_loss` (the `extra_penalties` list) and `training/checkpoint.py`.

**What M1 must do (cheap):**
- Route the loss through `assemble_loss(model, x, y, extra_penalties=())` with an **empty list** (Pattern 3). M1 passes nothing; the plumbing exists.
- Ensure the training loop holds a **reference to the model and can iterate `model.named_parameters()`** at step time — already true, just don't hide the model from the loss function.
- Make `checkpoint.py`'s save/load dict **open to extra keys** (it's already a dict) so M2 can stash Fisher information and a parameter snapshot (`theta_star`) alongside weights without changing the format.

**What M2 will add (do NOT build now):** An `ewc.py` that, after a task finishes, estimates the diagonal Fisher information (squared gradients over a data sample) and stores `{fisher, theta_star}` in the checkpoint. The penalty `lambda/2 * Σ fisher_i * (theta_i - theta_star_i)^2` becomes one entry appended to `extra_penalties`. The training loop and checkpoint format do not change.

**M1 acceptance for this seam:** loss goes through `assemble_loss` with an empty penalty list; checkpoints are dicts. Do not compute Fisher, do not store snapshots, do not add lambda.

### Why these seams are safe (not scope creep)

Both seams are **structural conventions, not features**: "use named `nn.Linear`" and "loss is a sum routed through one function" are *good design at M1 regardless of M2*. They add no behavior, no tests beyond what M1 already needs, and no runtime cost. The anti-pattern they prevent — fusing all attention math into one custom op, or inlining cross-entropy in the loop — would force a painful M2 rewrite of the model and trainer. Spending 5 lines now to avoid that is the correct trade.

## Anti-Patterns

### Anti-Pattern 1: Scattered device/`.cuda()` calls

**What people do:** Sprinkle `.cuda()`, `torch.cuda.amp`, and `if torch.cuda.is_available()` throughout model and data code.
**Why it's wrong:** Breaks the laptop-CPU path in a dozen places; every fix is a scavenger hunt. Directly violates the dual-environment requirement.
**Do this instead:** One `RuntimeConfig` resolves device + AMP once; everything reads from it (Pattern 1). Model code is device-agnostic.

### Anti-Pattern 2: Fusing attention into one monolithic custom op

**What people do:** Hand-roll all of QKV projection + scores + output projection as raw tensor math / `F.linear` with bare weight tensors for "efficiency."
**Why it's wrong:** Leaves no named `nn.Linear` for M2's LoRA to wrap, forcing a model rewrite. Also harder to unit-test the causal mask in isolation.
**Do this instead:** Compose attention from named `nn.Linear` submodules (Seam A). At 15M params the "fusion" speedup is irrelevant; clarity and extensibility win.

### Anti-Pattern 3: Inlining the loss in the training loop

**What people do:** Write `loss = F.cross_entropy(...)` directly inside the step loop.
**Why it's wrong:** EWC (M2) then has to surgically edit the loop. Also tangles logging.
**Do this instead:** Route through `assemble_loss` with a (M1-empty) penalty list (Pattern 3 / Seam B).

### Anti-Pattern 4: Bare `model.state_dict()` checkpoints

**What people do:** `torch.save(model.state_dict(), path)`.
**Why it's wrong:** Loading on the laptop needs the architecture config out-of-band; resumability needs optimizer + step + RNG. EWC (M2) needs to co-store Fisher info.
**Do this instead:** Self-describing checkpoint dict (Pattern 4) that already accepts extra keys.

### Anti-Pattern 5: Logic living in Kaggle notebooks

**What people do:** Write the training loop / model directly in `.ipynb` cells.
**Why it's wrong:** Untestable, unreviewable, and impossible to reuse on the laptop. Notebooks rot.
**Do this instead:** All logic in `src/personacore/`; notebooks import and call. The notebook is ~20 lines of wiring.

### Anti-Pattern 6: Tokenizer/checkpoint version drift

**What people do:** Retrain the tokenizer (or change vocab size) after a model is trained.
**Why it's wrong:** Vocab mismatch silently corrupts generation — embeddings index a different vocab.
**Do this instead:** Treat `tokenizer.json` as a frozen artifact tied to the checkpoint; pin vocab_size in `ModelConfig` and serialize it in the checkpoint.

## Scaling Considerations

Scaling here means *model/data size within the free-tier budget*, not user count.

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Smoke test (laptop CPU) | `train_cpu_smoke.yaml`: tiny dims, ~10 steps. Validates the *whole pipeline* end-to-end without a GPU. The AMP-disabled CPU path makes this a few-second run. |
| Full M1 (~10–15M, P100) | fp16 AMP + GradScaler; `np.memmap` data loading; gradient checkpointing *not* needed at 15M (P100 16GB has ample headroom). Checkpoint every N steps for 30h/week resumability. |
| M2 (LoRA/EWC, same P100) | LoRA *reduces* trainable params (only adapters train), so memory drops — no architecture change needed. EWC adds a Fisher tensor (~1x param size in memory during penalty); fine at 15M. |

### Scaling Priorities

1. **First constraint: Kaggle wall-clock (30h/week), not memory.** At 15M params on a 16GB P100, you're compute/time-bound, not memory-bound. Prioritize checkpoint-resume robustness and a fast data loader (`memmap`) over memory tricks.
2. **Second constraint: laptop CPU inference latency.** Generation is autoregressive (one forward per token). Keep the model genuinely ~10–15M and consider a simple KV-cache as an M2-era optimization if the demo feels slow — but only if measured. Don't pre-optimize.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Kaggle (P100, notebooks) | `pip install -e .` the package; notebook imports `personacore`, runs `train(cfg)` | No internet at inference required; download checkpoint + tokenizer artifacts out |
| TinyStories dataset | One-time download → `prepare_data.py` → `.bin` | Encode once, memmap thereafter |
| Gradio (local demo) | `app/demo_gradio.py` imports `generation.sampler` + loads checkpoint on CPU | Fully on-device; satisfies privacy/no-store requirement |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `tokenizer/` ↔ `data/` | `data/prepare.py` calls `tokenizer.encode` | Tokenizer is a frozen artifact; one-directional |
| `data/` ↔ `training/` | `loader.get_batch()` returns device-placed tensors | Loader owns device placement (reads RuntimeConfig) |
| `model/` ↔ `training/` | Trainer calls `model(x, y)`; model returns `(logits, loss)` | Model is pure; trainer owns all state. **Hard boundary — model never imports training.** |
| `model/` ↔ `generation/` | `sampler.generate` calls `model(idx)` (no targets) | Same pure-forward contract |
| `training/losses` ↔ M2 EWC | `extra_penalties` list | The EWC seam (Seam B) |
| `model/*.Linear` ↔ M2 LoRA | named `nn.Linear` attributes | The LoRA injection seam (Seam A) |

## Confidence Assessment

| Area | Confidence | Basis |
|------|------------|-------|
| nanoGPT-style structure (model.py/train.py/sample.py/config split, memmap data) | HIGH | Verified against karpathy/nanoGPT reference; de facto standard for this exact task |
| torch.amp device-agnostic API (`autocast(device_type=...)`, `GradScaler`, CPU=fp32 default) | HIGH | Verified against current PyTorch AMP docs |
| LoRA injection seam (wrap named `nn.Linear` via recursive module replacement) | HIGH | Verified as the standard from-scratch LoRA pattern across multiple reference implementations |
| EWC seam (diagonal Fisher + theta_star penalty as an additive loss term) | HIGH | Standard EWC formulation; the *seam* (pluggable loss term + open checkpoint dict) is a conservative, well-understood design |
| P100-specific AMP guidance (fp16 modest gain, no bf16) | MEDIUM | Pascal architecture limitation is well established; exact speedup is model-dependent and unmeasured here |

## Sources

- [karpathy/nanoGPT](https://github.com/karpathy/nanoGPT) — reference structure: `model.py`, `train.py`, `sample.py`, `configurator.py`, memmap data loading (HIGH)
- [karpathy/nanoGPT model.py](https://github.com/karpathy/nanoGPT/blob/master/model.py) and [train.py](https://github.com/karpathy/nanoGPT/blob/master/train.py) — pure-model/stateful-trainer split, checkpoint dict pattern (HIGH)
- [PyTorch torch.amp package docs](https://docs.pytorch.org/docs/stable/amp.html) and [AMP examples](https://docs.pytorch.org/docs/stable/notes/amp_examples.html) — device-agnostic `autocast(device_type=...)`, `GradScaler`, bf16-needs-no-scaler (HIGH)
- [PyTorch AMP recipe](https://docs.pytorch.org/tutorials/recipes/recipes/amp_recipe.html) — enabling/disabling AMP cleanly via the `enabled` flag (HIGH)
- [Implementing LoRA from scratch (TDS)](https://towardsdatascience.com/implementing-lora-from-scratch-20f838b046f1) and [LoRA-Torch reimplementation](https://github.com/Baijiong-Lin/LoRA-Torch) — recursive `nn.Linear` injection / wrapper pattern (MEDIUM-HIGH)

---
*Architecture research for: from-scratch small GPT-style language model (PyTorch, dual-environment)*
*Researched: 2026-06-04*
