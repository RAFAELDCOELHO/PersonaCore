<!-- GSD:project-start source:PROJECT.md -->
## Project

**PersonaCore**

PersonaCore is a conversational AI assistant where **all** memory and personalization live in the model weights — no databases, no vector stores, no external files. The model learns who you are by updating its own parameters, making weight-based memory a privacy guarantee by design. The entire stack (GPT-style transformer decoder, BPE tokenizer, LoRA adapters, EWC continual learning) is built from scratch in PyTorch and runs fully on-device. It is an elite CS-undergraduate portfolio project intended to demonstrate deep ML fundamentals, a genuinely novel approach, and a working demo.

**Core Value:** The novel claim must be true and demonstrable: **personalization lives in the weights, not in a prompt or a store** — and the from-scratch implementation must be correct enough to prove it. If everything else fails, the project must still show real ML depth built by hand.

### Constraints

- **Budget**: Zero — only Kaggle free-tier GPU (P100 16GB, 30h/week). No paid compute or APIs.
- **Tech stack**: Python + PyTorch only. No HuggingFace PEFT/transformers model code; core ML components built from scratch.
- **Compute/Model size**: ~10–15M parameters — chosen to fit free-tier training time and on-device CPU inference.
- **Portability**: Must train on Kaggle GPU and run inference/demo on a laptop CPU with no internet.
- **Privacy**: Memory must live in weights only — no external data stores. This is a design requirement, not just a constraint.
- **Dev environment**: Claude Code as the development environment; GSD workflow for planning.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## TL;DR Prescription
- **Train on Kaggle's pre-installed PyTorch** (do not reinstall torch in the notebook). For local CPU dev, pin `torch==2.7.*` (the last release line that still ships a Pascal-capable CUDA wheel and a clean CPU wheel) — but the GPU build only matters on Kaggle, and there you use whatever Kaggle ships.
- **CRITICAL P100 constraint:** P100 is Pascal, compute capability **6.0**. PyTorch wheels built with **CUDA 12.8+ (`cu128`, `cu129`, `cu130`) dropped Pascal `sm_60` kernels.** Only **`cu126` (CUDA 12.6) and earlier** wheels contain Pascal binaries. This is the single most important compatibility fact in this milestone. (See Version Compatibility section.)
- **No bf16.** P100 has no Tensor Cores and no bf16 support. Mixed precision = **fp16 AMP + `GradScaler`** only, and the speedup is modest (memory savings are the real win, not throughput).
- **Tokenizer: from scratch** (pure Python/regex + dict merges). `tiktoken` / HF `tokenizers` are reference oracles for unit tests only, never the implementation.
- **Logging: offline CSV + matplotlib.** No wandb/online tooling — violates zero-budget/offline/on-device intent and adds a network dependency Kaggle sessions don't need.
## Recommended Stack
### Core Technologies
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **Python** | 3.11 (3.10–3.12 ok) | Language runtime | Kaggle images and modern PyTorch target 3.11; 3.11 is the stable sweet spot. Avoid 3.13+ for fewer wheel surprises on the laptop. |
| **PyTorch (`torch`)** | Kaggle: use pre-installed; Local: `2.7.*` (CPU) | Tensors, autograd, nn, optimizer, AMP | Industry-standard from-scratch DL framework. `nn.Module`, `F.scaled_dot_product_attention`, `torch.amp`, `torch.save/load` give everything needed without HF model code. 2.7.x is the newest line whose CUDA wheels still include Pascal `sm_60`; later lines (2.8+) only ship Pascal in `cu126` builds and CPU wheels (which is fine for the laptop). |
| **NumPy** | 2.x (`>=1.26,<3`) | Token-array memmap, eval metrics, plotting glue | The standard way to store the pre-tokenized corpus as a flat `uint16` memmap and sample contiguous training windows cheaply. PyTorch 2.7 supports NumPy 2.x. |
| **Gradio** | 5.x (`>=5,<6`) | Local web-UI chat demo (on-device) | `gr.ChatInterface` gives a streaming chat UI in ~20 lines, runs fully local (`launch()` binds localhost), zero frontend code, great for demo video/screenshots. Gradio 5 is the current stable major with a refreshed chat UI and streaming. |
### Supporting Libraries
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **pytest** | 8.x | Unit tests for bigram, BPE, attention/MLP/blocks, sampling | First-class deliverable per PROJECT.md. Use parametrized tests + tiny fixtures; assert shapes, causal-mask correctness, encode/decode round-trips, and reference-equivalence vs `tiktoken`. |
| **matplotlib** | 3.9+ | Training-curve and sampling figures for `demo.ipynb` | Offline plotting of loss/lr curves read back from the CSV log. No online dashboard needed. |
| **tqdm** | 4.66+ | Progress bars in the training loop + tokenizer training | Lightweight, works in notebooks and terminals; useful for the long BPE merge loop and per-step training feedback. |
| **requests** *(optional)* | 2.32+ | Download TinyStories `.txt` directly in the notebook | Only if not using Kaggle Datasets attach. A single `resolve/main/...txt` GET is enough; no `datasets`/`huggingface_hub` required. |
| **safetensors** *(optional but recommended)* | 0.4+ | Portable, secure checkpoint format for the final model weights | Loading a `torch.save` pickle across machines is fine but executes arbitrary code; `safetensors` is a zero-dependency, framework-agnostic, safe format ideal for the shippable laptop demo weights. Keep optimizer state in a separate `torch.save` for resumability. |
### Development Tools
| Tool | Purpose | Notes |
|------|---------|-------|
| **venv + requirements.txt** | Reproducible local environment | PROJECT.md explicitly requires this. Pin torch to a CPU wheel locally: `torch==2.7.* --index-url https://download.pytorch.org/whl/cpu`. |
| **ruff** *(optional)* | Lint + format | Single fast tool; replaces black+flake8+isort. Nice-to-have for portfolio polish, not required. |
| **Kaggle Notebooks** | GPU training environment | Attach TinyStories as a Kaggle Dataset (upload once) to avoid re-downloading each session and to work offline within the session. Use the persistent `/kaggle/working` for checkpoints; download checkpoints between the 9h-session / 30h-week limits. |
| **Jupyter / nbconvert** | `demo.ipynb` research artifact | The notebook is a deliverable (training curves, sampling). Keep heavy training out of it; it loads a checkpoint + the CSV log and renders the narrative. |
## Installation
# ---- Local laptop (CPU inference + dev + tests) ----
# CPU-only PyTorch (Pascal wheel issues are irrelevant on CPU)
# Core + demo + dev
# requests only if downloading TinyStories at runtime instead of Kaggle Dataset attach
# ---- Kaggle notebook: do NOT pip install torch ----
# Kaggle ships a P100-compatible torch already. Verify, don't replace:
# Expect a Tesla P100-PCIE-16GB and a torch built against a Pascal-capable CUDA (<=12.6).
# ---- TinyStories direct download (no paid service, no HF datasets lib needed) ----
# V2 (GPT-4-only) is the higher-quality corpus; recommended for best fluency-per-param.
# train ~2.23 GB, valid ~22.5 MB. Plain UTF-8 text, stories separated by <|endoftext|>.
## TinyStories Data Tooling (zero-budget, offline)
- **Use `TinyStoriesV2-GPT4-*`** (GPT-4-only) over the original mixed `TinyStories-*` — higher quality, better coherence-per-parameter at 10–15M.
- **Preprocessing pipeline (from scratch):** raw `.txt` → train BPE → encode full corpus once → store as a flat `np.uint16` memmap on disk (`train.bin`, `val.bin`). Training samples random contiguous windows from the memmap. This is the nanoGPT-style pattern: cheap, RAM-light, and re-reads nothing.
- **`<|endoftext|>` handling:** treat the document separator as a single special token reserved in the tokenizer; do not let BPE merge across it.
## Training Utilities (P100-specific)
| Concern | Recommendation | Rationale |
|---------|----------------|-----------|
| **Mixed precision** | `torch.amp.autocast(device_type="cuda", dtype=torch.float16)` + `torch.amp.GradScaler()` | P100 supports fp16 storage/compute but has **no Tensor Cores** → speedup is modest; the real benefit is ~halved activation memory, letting you use a larger batch/context. fp16 needs `GradScaler` to prevent gradient underflow. **bf16 is unavailable on Pascal** — do not use it. |
| **Gradient accumulation** | Accumulate N micro-batches before `optimizer.step()` | Achieve an effective large batch on 16 GB. Standard pattern: divide loss by accumulation steps, `scaler.scale(loss).backward()` each micro-batch, step+update every N. |
| **Checkpointing / resumability** | Save `{model, optimizer, scaler, step, rng_state, config}` to `/kaggle/working` every K steps | Kaggle sessions cap at ~9h and 30h/week, so resumable training is mandatory (PROJECT.md calls this out). Keep a `latest.pt` (full state, `torch.save`) for resume and export `model.safetensors` for the portable demo. |
| **Optimizer** | `torch.optim.AdamW` + cosine decay w/ warmup (hand-rolled LR schedule) | Standard for GPT pretraining. Writing the schedule by hand fits the from-scratch ethos and is trivial. |
| **Attention kernel** | `torch.nn.functional.scaled_dot_product_attention` (is_causal=True) is allowed | It's a math primitive, not model code — keeps you honest to "from scratch" while avoiding a naive slow softmax. If the portfolio narrative wants to *show* the manual attention, implement both and unit-test equivalence. (Note: the fused FlashAttention backend won't engage on Pascal; PyTorch falls back to the math backend automatically — correct, just not fast.) |
| **`torch.compile`** | **Skip on P100** | Inductor/Triton GPU codegen historically has poor/unsupported Pascal support and adds compile-time and flakiness. Not worth it at 10–15M params. |
| **Memory headroom** | 10–15M params is tiny; bottleneck is batch×context activations | At this scale you'll likely be compute/time-bound, not memory-bound. fp16 AMP + grad accumulation is plenty; no need for activation checkpointing. |
## Experiment Logging (offline)
| Approach | Recommendation |
|----------|----------------|
| **CSV + matplotlib** | **Use this.** Append `step,train_loss,val_loss,lr,tokens,wall_clock` to a CSV each eval interval. `demo.ipynb` reads the CSV and plots curves. Zero dependencies, zero network, fully reproducible, survives session restarts (just append). |
| **TensorBoard** *(optional)* | Acceptable offline alternative if you want interactive curves; `torch.utils.tensorboard` is built in. Heavier than CSV and the event files are clunky to ship — CSV is preferred for a portfolio artifact. |
| **wandb / Comet / Neptune** | **Do NOT use.** Require accounts/API keys and network calls — violate the zero-budget, offline, on-device, privacy-by-design constraints. They also clutter a "self-implemented" narrative with a SaaS dependency. |
## Alternatives Considered
| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Pre-tokenized `uint16` memmap (`.bin`) | HF `datasets` streaming | If you outgrow the laptop's disk for a much larger corpus and need on-the-fly tokenization — not the case at TinyStories/10–15M scale. |
| CSV + matplotlib logging | TensorBoard (offline) | If you specifically want interactive zoom/compare across runs and don't mind shipping event files. |
| Gradio 5 `ChatInterface` | Streamlit / FastAPI+HTML / plain CLI | Streamlit if you prefer a dashboard layout; a CLI `generate.py` is a fine *additional* artifact but weaker for a demo video. |
| `safetensors` for weights | Plain `torch.save(state_dict)` | `torch.save` is fine when loading only your own trusted file; prefer it for the *resume* checkpoint (needs optimizer/scaler state). Use `safetensors` for the *shippable* weights. |
| `torch==2.7.*` local pin | Newest `torch` (2.12) CPU wheel | The newest CPU wheel works locally too (Pascal issue is GPU-only). Pin a known-good version for reproducibility; bumping later is low-risk on CPU. |
## What NOT to Use
| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **HuggingFace `transformers` model code** | Excluded by design — the portfolio value is a hand-built transformer. | Your own `nn.Module` blocks (attention, MLP, embeddings). |
| **HuggingFace `peft`** | Excluded by design (and out of M1 scope entirely). | From-scratch LoRA in M2. |
| **`tiktoken` / HF `tokenizers` as the implementation** | BPE is a from-scratch deliverable; using them as the tokenizer defeats the purpose. | Hand-rolled BPE (train/encode/decode). Use `tiktoken` **only** as a reference oracle in unit tests to validate encode/decode behavior. |
| **CUDA 12.8+ PyTorch wheels (`cu128`/`cu129`/`cu130`) on P100** | These wheels **dropped Pascal `sm_60` kernels** → CUDA ops fail or fall back/crash on P100. | On Kaggle: use the pre-installed torch (Pascal-capable). If ever installing manually for a Pascal GPU: a `cu126` wheel or earlier. |
| **bf16 / `torch.bfloat16` on GPU** | Pascal has no bf16 support. | fp16 AMP + `GradScaler`. |
| **`torch.compile` on P100** | Poor/unsupported Pascal codegen, compile overhead, flakiness; negligible benefit at this scale. | Plain eager mode (+ `sdpa` math backend). |
| **wandb / Comet / Neptune** | Network + account dependency; violates offline/zero-budget/privacy intent. | CSV + matplotlib (or offline TensorBoard). |
| **HF `datasets` as the runtime data path** | Heavy dependency + implicit network calls during training. | Direct `.txt` download once → Kaggle Dataset attach → `uint16` memmap. |
| **Reinstalling `torch` inside the Kaggle notebook** | Risks pulling a non-Pascal `cu128+` wheel and breaking GPU training; wastes session time. | Use Kaggle's pre-installed, P100-validated torch. Verify with `torch.cuda.get_device_name(0)`. |
| **Multi-GPU / DDP / FSDP, flash-attn pip package** | Out of scope (single P100); `flash-attn` doesn't support Pascal. | Single-device training; `F.scaled_dot_product_attention` (math backend). |
## Stack Patterns by Variant
- Use the pre-installed PyTorch; verify device + CUDA version at notebook start.
- Attach TinyStories as a Kaggle Dataset; keep the session offline.
- fp16 AMP + `GradScaler` + gradient accumulation; checkpoint to `/kaggle/working` every K steps and download `latest.pt` before the session ends.
- CPU-only torch wheel; load `model.safetensors`, run `model.eval()` + `torch.no_grad()`.
- Gradio `ChatInterface` with streaming token generation (temperature + top-k sampling).
- Run `pytest` here; tests must not require a GPU.
- Resume from `latest.pt` (restores model + optimizer + scaler + step + RNG). This is why optimizer/scaler/RNG state must be in the checkpoint, not just the weights.
## Version Compatibility
| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| **P100 (Pascal, sm_60)** | PyTorch CUDA wheels **`cu126` or earlier** | **`cu128`/`cu129`/`cu130` dropped Pascal binaries (PyTorch 2.8 deprecated, CUDA 13 removed Maxwell/Pascal/Volta).** This is the load-bearing constraint. On Kaggle the pre-installed torch is already Pascal-valid — just don't replace it. |
| **P100** | fp16 AMP only | No Tensor Cores, no bf16. fp16 needs `GradScaler`. |
| `torch` 2.7.x | NumPy 2.x, Python 3.10–3.12 | Stable, widely supported combo; last line with broad Pascal CUDA-wheel coverage. |
| `torch` 2.12.0 (latest, May 2026) | CPU wheel fine on laptop | Latest release; its `cu128+` GPU wheels are **not** P100-compatible — irrelevant for CPU inference, relevant if you ever try to GPU-train outside Kaggle. |
| Gradio 5.x | Python 3.10+, FastAPI/Starlette (bundled) | Pin `<6` to avoid a future major bump; `launch()` is fully local/offline. |
| `safetensors` 0.4+ | torch any recent | Framework-agnostic; load weights without executing pickled code. |
## Sources
- https://pytorch.org/get-started/locally/ — current PyTorch install matrix & supported CUDA (HIGH)
- https://pypi.org/project/torch/ — latest release is torch 2.12.0 (2026-05-13) (HIGH)
- https://github.com/pytorch/pytorch/issues/157517 — "Delete support for Maxwell/Pascal/Volta for CUDA 12.8/12.9 builds"; `cu126` retains Pascal, `cu128`+ drops it (HIGH — load-bearing P100 fact)
- https://github.com/pytorch/pytorch/issues/159980 — CUDA support matrix for 2.9 (CUDA 12.6/12.8/13.0) (MEDIUM)
- https://docs.pytorch.org/docs/stable/amp.html + AMP recipe — fp16 autocast + GradScaler usage; bf16 recommended only on Ampere+ (HIGH)
- https://huggingface.co/datasets/roneneldan/TinyStories/tree/main — TinyStoriesV2-GPT4 train (2.23 GB) / valid (22.5 MB) direct `resolve/main/...` URLs (HIGH)
- https://www.gradio.app/changelog + https://huggingface.co/blog/gradio-5 — Gradio 5 stable, ChatInterface streaming, local launch (HIGH)
- Kaggle hardware: Tesla P100-PCIE 16 GB, 30h/week, ~9h/session (MEDIUM — community/docs corroborated; verify `torch.__version__` in-notebook)
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
