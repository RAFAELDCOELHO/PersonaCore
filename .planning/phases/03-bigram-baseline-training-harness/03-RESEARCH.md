# Phase 3: Bigram Baseline & Training Harness - Research

**Researched:** 2026-06-04
**Domain:** From-scratch PyTorch training harness (loop, AMP, LR schedule, checkpoint/resume, data split, sampling) de-risked on a trivial bigram LM
**Confidence:** HIGH (every recommendation grounded in the actual repo code: `config.py`, `checkpoint.py`, `logging.py`, `seeding.py`, tokenizer; PyTorch AMP/scheduler facts cited from official docs)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Lookup-table bigram, GPT-shaped. Karpathy-canonical `BigramLanguageModel`: `nn.Embedding(vocab_size, vocab_size)` where `logits = table(idx)` with shape `(B, T, V)`. The ~67M lookup-table params are irrelevant (throwaway de-risk model, never pretrained).
- **D-02:** `forward(idx, targets=None) -> (logits, loss)` is the LOCKED model↔harness contract — the *same* signature Phase-4's GPT will implement. `forward` computes base cross-entropy internally: returns `(logits, base_loss)` when `targets` is given, `(logits, None)` otherwise.
- **D-02a:** Reshape discipline for CE: `logits.view(B*T, V)` vs `targets.view(B*T)` — standard nanoGPT flatten.
- **D-03:** Loss is assembled in the TRAINING LOOP, not the model. The training step calls `total = assemble_loss(base_loss, extra_penalties=())`. The model stays pure (only base CE).
- **D-04:** `assemble_loss(base_loss, extra_penalties=()) -> base_loss + sum(extra_penalties)`. Each item is a precomputed scalar tensor. M1 passes `()` → returns `base_loss` unchanged (identity). No callbacks, no lazy callables.
- **D-04a:** Unit-test the seam in M1 even though no penalty exists: assert empty-tuple identity and additive behavior with a dummy penalty tensor.
- **D-05:** Reuse the existing `src/personacore/checkpoint.py` `save_checkpoint`/`load_checkpoint` **unchanged** — already an open dict with full RNG restore and `**extra` seam. Phase 3 drives it end-to-end. **Inherited constraint:** `save_checkpoint` calls `scheduler.state_dict()`, so the LR schedule must be a `torch.optim.lr_scheduler` object, not a bare function.

### Claude's Discretion
- **D-06 — Harness data path (lean):** Train on a small committed text fixture (a handful of TinyStories-style docs separated by `<|endoftext|>`) encoded on-the-fly via the frozen Phase-2 tokenizer (`eos_id=8184`). Produce an in-memory / tiny on-disk `uint16` token array, sample random contiguous windows (nanoGPT `get_batch`). **Do NOT build the full-corpus memmap or fetch full TinyStories** (Phase 5). Fixture must contain ≥2 docs so the doc-level split demonstrably has no leakage.
- **D-07 — AMP-on-CPU-CI verification (lean):** fp16-AMP+GradScaler path is GPU-only; CI is CPU-only. Keep `scale → backward → unscale_ → clip → step → update` honest via (a) a CPU-runnable unit test asserting the *ordering*, and (b) a GPU-conditional (`@pytest.mark.skipif(not cuda)`) smoke test. fp32 is default everywhere.
- **D-08 — LR schedule mechanics:** Hand-rolled warmup + cosine implemented as a `torch.optim.lr_scheduler.LambdaLR` (resumable via `state_dict()`). Optimizer is `torch.optim.AdamW` with `weight_decay` and `grad_clip` from `TrainConfig`.
- **D-09 — Module layout:** `src/personacore/model/bigram.py`, `src/personacore/training/` (`loop.py`, `loss.py`, `data.py`, `schedule.py`), thin `scripts/train_bigram.py` (**no CLI/argparse**; defaults/kwargs only). Phase 4 adds `model/gpt.py` beside the bigram, reusing `training/` untouched.
- **D-10 — Overfit gate (TRAIN-05):** Drive loss toward ~0 on one fixed batch over a bounded step budget; assert final loss below a small threshold. CPU-only, fast, deterministic via the Phase-1 `seeding` utilities.
- **D-11 — Minimal sampling:** Only enough sampling (greedy/temperature next-token loop) to prove the harness produces text output. The full `generate()` is Phase 6.

### Deferred Ideas (OUT OF SCOPE)
- GPT decoder, attention/MLP/blocks, weight tying, param sizing — Phase 4 (MODEL-02..07).
- Full-corpus `uint16` memmap + TinyStories fetch + the real pretraining run — Phase 5 (PRE-01..03).
- Full `generate()` (top-k/top-p, EOS-aware stop) + its tests — Phase 6 (GEN-01..03).
- EWC Fisher-penalty computation, LoRA adapters — Milestone 2. Phase 3 wires the *empty* `assemble_loss` seam and the open-dict `**extra` slot only.
- Architecture/LR ablation table — Phase 7 (EVAL-03).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MODEL-01 | Bigram LM baseline from scratch, de-risks the harness | `nn.Embedding(V, V)` lookup-table model with the locked `forward(idx, targets) -> (logits, loss)` contract (§Bigram Model). |
| TRAIN-01 | Training loop: AdamW + warmup/cosine LR + grad clip + configurable grad accum | §Training Loop + §Gradient Accumulation + §LR Schedule, all wired to `TrainConfig` fields. |
| TRAIN-02 | fp32 default; optional fp16-AMP+GradScaler with unscale-before-clip | §AMP Discipline — exact step ordering + the CPU-testable ordering seam (§Validation Architecture). |
| TRAIN-03 | Train/val split with periodic validation loss; no leakage | §Data Path — doc-level split on `eos_id=8184`, `get_batch` window sampler, leakage assertion. |
| TRAIN-04 | Offline CSV+matplotlib logging that survives restarts; curves reproducible | Reuse `CSVLogger`; §Checkpoint/Resume proves the curve reproduces across kill+resume. |
| TRAIN-05 | Overfit-a-single-batch test (harness correctness gate) | §Overfit Gate — fixed batch, bounded budget, threshold, deterministic via `seed_everything`. |
| TRAIN-06 | `assemble_loss(..., extra_penalties=())` seam + open-dict checkpoints (M2 EWC seam) | §`assemble_loss` Seam (identity-on-empty) + reuse `checkpoint.py` `**extra` (already proven by `test_open_dict_extensible`). |
</phase_requirements>

## Summary

Phase 3 is a **harness phase, not a model phase**. The bigram (`nn.Embedding(vocab_size, vocab_size)`) is a one-line throwaway whose only purpose is to exercise the `forward(idx, targets) -> (logits, loss)` contract so the *real* deliverables — the train loop, AMP discipline, LR schedule, checkpoint/resume, doc-level split, CSV logging, and the `assemble_loss` seam — fail loudly now (cheap, CPU) instead of during Phase-4 transformer bring-up (expensive). Every load-bearing primitive already exists in the repo: `RuntimeConfig.autocast()` (single AMP source of truth), `save_checkpoint`/`load_checkpoint` (open-dict, full RNG restore, already passing a kill-and-resume trajectory test), `CSVLogger` (append-only, restart-safe), `seed_everything` (fresh-run seeding), and the frozen tokenizer (`from_json("artifacts/tokenizer.json")`, `eos_id=8184`). Phase 3's job is to **drive these existing pieces end-to-end**, adding only `model/bigram.py` and `training/{loop,loss,data,schedule}.py` plus a thin `scripts/train_bigram.py`.

The two highest-risk seams are (1) the **AMP step ordering** — `scaler.scale(loss).backward()` → `scaler.unscale_(optimizer)` → `clip_grad_norm_` → `scaler.step(optimizer)` → `scaler.update()` — which must compose correctly with gradient accumulation, and which CI must verify *on CPU where AMP is a no-op*; and (2) **resume trajectory equality** — a save→kill→resume must reproduce the identical loss curve. The existing `test_checkpoint.py::test_resume_identical_trajectory` already proves the checkpoint mechanism restores RNG *state* (not a re-seed) bit-identically within 1e-6 for a toy `nn.Linear`; Phase 3 extends that exact pattern to the bigram + the real LambdaLR schedule + the CSV log.

**Primary recommendation:** Build five thin from-scratch modules (`bigram.py`, `loss.py`, `schedule.py`, `data.py`, `loop.py`) that consume — never re-implement — the existing config/checkpoint/logging/seeding primitives, plus CPU-only tests for each seam. The single biggest correctness risk is AMP step *ordering*; make it an explicit, CPU-assertable function boundary (see §AMP Discipline and §Validation Architecture). Use `LambdaLR` for the schedule (satisfies the `scheduler.state_dict()` checkpoint contract). Keep fp32 the default everywhere.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Bigram model (forward → logits, base CE) | `model/bigram.py` | — | Model owns base loss only (D-02/D-03); stays pure for M2 EWC. |
| Loss assembly (`assemble_loss`) | `training/loss.py` | — | Loop-level extension point (D-03); model never sees penalties. |
| LR schedule (warmup+cosine lambda) | `training/schedule.py` | `torch.optim.lr_scheduler.LambdaLR` | Must be a scheduler object for `state_dict()` (D-05/D-08). |
| Data: fixture → tokens → split → batch | `training/data.py` | frozen tokenizer (`from_json`) | Doc-level split on `eos_id` (D-06); nanoGPT `get_batch`. |
| Train step (AMP, grad accum, clip, step) | `training/loop.py` | `RuntimeConfig.autocast()` + `GradScaler` | Orchestrates the AMP/accum/clip ordering (TRAIN-01/02). |
| Device/precision resolution | `RuntimeConfig` (existing) | — | Single source of AMP truth — loop must NOT call `torch.cuda.*`. |
| Checkpoint/resume (model+opt+sched+RNG) | `checkpoint.py` (existing) | — | Reuse unchanged (D-05); already RNG-state-restoring. |
| Offline logging | `CSVLogger` (existing) | — | Reuse unchanged; append-only, restart-safe (TRAIN-04). |
| Seeding / determinism | `seed_everything` (existing) | — | Fresh-run seed only; resume restores state, never re-seeds. |
| Minimal sampling (see output) | `model/bigram.py` or `training/loop.py` | — | Greedy/temperature loop only (D-11); full `generate()` is Phase 6. |
| Entry point | `scripts/train_bigram.py` | — | Thin, no argparse (Phase-1 D-04); kwargs/defaults only. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `torch` | Kaggle pre-installed / local CPU `2.7.*` | `nn.Embedding`, `F.cross_entropy`, `AdamW`, `lr_scheduler.LambdaLR`, `amp.GradScaler`, `clip_grad_norm_` | Already the project's only ML dep; all primitives needed for the harness are stdlib-of-torch. `[CITED: CLAUDE.md / STACK.md]` |
| `numpy` | `>=1.26,<3` | `uint16` token array (in-memory / tiny on-disk), `get_batch` index draw | nanoGPT data idiom; already a core dep. `[CITED: STACK.md]` |
| `personacore` (internal) | this repo | `RuntimeConfig`/`ModelConfig`/`TrainConfig`, `save/load_checkpoint`, `CSVLogger`, `seed_everything`, `BPETokenizer`/`from_json` | All Phase-1/2 primitives the harness drives. `[VERIFIED: repo grep]` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | `~=9.0` (per `pyproject.toml [dev]`) | CPU-only seam tests | Every Phase-3 test; the AMP GPU smoke test guards with `skipif(not cuda)`. `[VERIFIED: pyproject.toml]` |
| `matplotlib` | 3.9+ | Loss-curve plotting from the CSV | Only needed when actually rendering curves; the harness *writes* CSV, Phase 8 `demo.ipynb` reads it. Phase 3 may add a tiny plot helper but the curve-reproducibility test reads the CSV directly (no matplotlib needed for the test). `[CITED: STACK.md]` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `LambdaLR` for warmup+cosine | A bare python `lr_lambda(step)` function called manually | REJECTED — `checkpoint.py` calls `scheduler.state_dict()` (D-05). A bare function has no `state_dict()` and would break resume. `LambdaLR` is the from-scratch-honest choice (you still write the lambda math by hand). `[VERIFIED: checkpoint.py L55]` |
| `LambdaLR` | `CosineAnnealingLR` + `LinearLR` + `SequentialLR` | Heavier, hides the math, and `SequentialLR` resume semantics are subtler. A single hand-written lambda is clearer for a portfolio and trivially resumable. `[ASSUMED]` |
| `F.cross_entropy` inside `forward` | Manual log-softmax + NLL | REJECTED — `F.cross_entropy` is a math primitive (same footing as `sdpa`), not "model code"; from-scratch ethos is satisfied. nanoGPT-canonical. `[ASSUMED]` |
| On-disk `.bin` token file | Pure in-memory numpy array | Either is fine at fixture scale. In-memory is simplest; a tiny on-disk `uint16` array better rehearses the Phase-5 memmap shape. Planner's call — D-06 allows both. `[CITED: CONTEXT.md D-06]` |

**Installation:** No new dependencies. The harness uses only `torch` + `numpy` + the internal package, all already declared. `matplotlib` is the only addition if a plot helper ships in Phase 3 (otherwise deferred to Phase 8). Verify before adding:
```bash
pip index versions matplotlib   # confirm current 3.9+ before declaring
```

## Package Legitimacy Audit

> No new external packages are introduced in Phase 3. All recommended libraries (`torch`, `numpy`, `pytest`) are already declared in `pyproject.toml` and were vetted in Phases 1-2. `matplotlib` (only if a plot helper ships now vs. Phase 8) is a long-established, high-trust scientific package.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| torch | PyPI | 9+ yrs | ~30M+/mo | github.com/pytorch/pytorch | not run (pre-vetted) | Approved (existing dep) |
| numpy | PyPI | 19+ yrs | ~300M+/mo | github.com/numpy/numpy | not run (pre-vetted) | Approved (existing dep) |
| pytest | PyPI | 15+ yrs | ~200M+/mo | github.com/pytest-dev/pytest | not run (pre-vetted) | Approved (existing dev dep) |
| matplotlib | PyPI | 22+ yrs | ~80M+/mo | github.com/matplotlib/matplotlib | not run (pre-vetted) | Approved (only if plot helper ships now) |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

*No installs introduced this phase, so the legitimacy gate is informational. If the planner elects to add `matplotlib` to a `[viz]` extra now, it is a household scientific package — no checkpoint needed.*

## Architecture Patterns

### System Architecture Diagram

```
                          scripts/train_bigram.py  (thin entry, no argparse)
                                       │  builds configs, seeds, calls train()
                                       ▼
  artifacts/tokenizer.json ──from_json──► BPETokenizer (FROZEN, eos_id=8184)
                                       │  encode(fixture_text)  ← tests/fixtures/bigram_corpus.txt (≥2 docs, eos-separated)
                                       ▼
                          training/data.py
            ┌──────────────────────────┴───────────────────────────┐
            │  1. encode → np.uint16 token array                    │
            │  2. doc-level split on eos_id (never mid-document)     │  ──► (train_ids, val_ids)   [no leakage]
            │  3. get_batch(split, batch_size, block_size) →        │
            │     random contiguous windows → (xb, yb) on device    │
            └──────────────────────────┬───────────────────────────┘
                                       ▼
                          training/loop.py  ── train_step / train()
        ┌──────────────────────────────┴──────────────────────────────────────────┐
        │  for step in range(max_steps):                                           │
        │    for micro in range(grad_accum_steps):           ← TrainConfig          │
        │       xb,yb = get_batch("train")                                          │
        │       with RuntimeConfig.autocast():               ← single AMP source    │
        │          logits, base_loss = model(xb, yb)         ← model/bigram.py D-02  │
        │       total = assemble_loss(base_loss, ())         ← training/loss.py D-04 │
        │       loss = total / grad_accum_steps              ← accum scaling         │
        │       scaler.scale(loss).backward()                ← GradScaler            │
        │    scaler.unscale_(optimizer)                      ← BEFORE clip           │
        │    clip_grad_norm_(params, grad_clip)              ← TrainConfig.grad_clip │
        │    scaler.step(optimizer); scaler.update()                                 │
        │    optimizer.zero_grad(set_to_none=True); scheduler.step()  ← LambdaLR     │
        │    if step % eval_interval == 0:                                           │
        │       val_loss = estimate_loss("val")  (model.eval()+no_grad)              │
        │       csv.log(step, train_loss, val_loss, lr, tokens, wall_clock)          │
        │       save_checkpoint(latest.pt, model,opt,sched,step,...)  ← every K      │
        └───────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
                          minimal sample(model, prompt_ids) → greedy/temperature loop → decode → text
                                       (D-11 — "see output" only; full generate() is Phase 6)
```

### Recommended Project Structure
```
src/personacore/
├── model/
│   ├── __init__.py
│   └── bigram.py          # BigramLanguageModel: nn.Embedding(V,V); forward(idx,targets)->(logits,loss)
├── training/
│   ├── __init__.py
│   ├── loss.py            # assemble_loss(base_loss, extra_penalties=()) -> base + sum(extra)
│   ├── schedule.py        # build_lr_lambda(warmup_steps, max_steps, min_lr_ratio) -> callable; LambdaLR factory
│   ├── data.py            # load_fixture -> tokens; split_documents(eos_id); get_batch(...)
│   └── loop.py            # train_step(...); train(...); estimate_loss(...); minimal sample(...)
scripts/
└── train_bigram.py        # thin: build configs, seed_everything, call train() — NO argparse
tests/
├── test_bigram_model.py   # forward contract: shapes, (logits,None) vs (logits,loss), CE flatten
├── test_assemble_loss.py  # identity-on-empty + additive (D-04a)
├── test_lr_schedule.py    # warmup ramp, cosine decay, state_dict() resume
├── test_data_split.py     # doc-level split, NO leakage, get_batch shapes/dtype/bounds
├── test_train_loop.py     # AMP step ORDERING (CPU); grad-accum equivalence
├── test_overfit_batch.py  # TRAIN-05 gate: loss -> ~0 on one fixed batch
└── test_resume_curve.py   # kill+resume reproduces the loss curve (extends test_checkpoint pattern)
```
Per Phase-1 D-11, `model/` and `training/` directories are created *by this phase* (no pre-stubbed empty dirs). Phase 4 later drops `model/gpt.py` beside `bigram.py` and reuses `training/` untouched.

### Pattern 1: GPT-shaped bigram (the locked contract)
**What:** A trivial lookup-table LM whose `forward` signature is identical to Phase-4's GPT.
**When to use:** As the de-risk model for the entire harness; never trained for real.
```python
# Source: nanoGPT/makemore canonical (Karpathy), adapted to D-02/D-02a contract
import torch.nn as nn
import torch.nn.functional as F

class BigramLanguageModel(nn.Module):
    def __init__(self, vocab_size: int):
        super().__init__()
        self.token_table = nn.Embedding(vocab_size, vocab_size)  # (V, V) lookup

    def forward(self, idx, targets=None):              # LOCKED signature (D-02)
        logits = self.token_table(idx)                  # (B, T, V)
        if targets is None:
            return logits, None
        B, T, V = logits.shape
        loss = F.cross_entropy(logits.view(B * T, V), targets.view(B * T))  # D-02a flatten
        return logits, loss                             # base CE only — no penalties (D-03)
```
Phase 4's GPT replaces only `__init__` and the body before the CE; the `(logits, loss)` return and the `.view` flatten are unchanged.

### Pattern 2: AMP step ordering with gradient accumulation (the critical seam)
**What:** The exact, order-sensitive AMP+accum+clip sequence.
**When to use:** Every training step; fp32 default makes the scaler a no-op (`enabled=False`) but the *ordering* is still exercised.
```python
# Source: PyTorch AMP recipe — gradient accumulation + clipping
# https://docs.pytorch.org/docs/stable/notes/amp_examples.html
optimizer.zero_grad(set_to_none=True)
for micro in range(grad_accum_steps):
    xb, yb = get_batch("train")
    with runtime.autocast():                      # RuntimeConfig.autocast() — single AMP source
        logits, base_loss = model(xb, yb)
        total = assemble_loss(base_loss, ())      # identity in M1
        loss = total / grad_accum_steps           # scale loss for accumulation
    scaler.scale(loss).backward()                 # accumulate scaled grads across micro-batches
scaler.unscale_(optimizer)                        # UNSCALE before clipping (mandatory order)
torch.nn.utils.clip_grad_norm_(model.parameters(), train_cfg.grad_clip)
scaler.step(optimizer)                            # skips step if grads are inf/nan
scaler.update()                                   # adjust scale factor
scheduler.step()                                  # per-OPTIMIZER-step, not per micro-batch
```
**Load-bearing facts** `[CITED: docs.pytorch.org/docs/stable/notes/amp_examples.html]`:
- `unscale_` must come **before** `clip_grad_norm_` — clipping operates on *unscaled* grads or the clip threshold is meaningless.
- Call `unscale_` **exactly once** per optimizer step (not per micro-batch).
- `scaler.step()` internally calls `unscale_` only if you didn't; calling it yourself first is the supported pattern for clipping.
- `scheduler.step()` fires once per optimizer step (after `scaler.update()`), never per micro-batch — otherwise the schedule advances `grad_accum_steps`× too fast.

### Pattern 3: GradScaler tied to the same enabled flag as autocast
**What:** Construct the scaler so it is a no-op exactly when AMP is off (CPU / fp32).
```python
# Source: torch.amp.GradScaler(enabled=...) — https://docs.pytorch.org/docs/stable/amp.html
from torch.amp import GradScaler
scaler = GradScaler(device=runtime.device.split(":")[0], enabled=runtime.amp)
```
`RuntimeConfig.amp` is already auto-disabled on CPU (`__post_init__` sets `amp=False` when `device=="cpu"`) and the bf16-on-Pascal guard already raises in the config — the loop must **not** re-derive any of this. When `enabled=False`, `scale()`/`unscale_()`/`step()`/`update()` are pass-throughs, so the *same code path* runs on CPU and the ordering test is meaningful. `[VERIFIED: config.py L44-53]`

### Pattern 4: Hand-rolled warmup + cosine as a LambdaLR
**What:** Linear warmup then cosine decay to a floor, as a resumable scheduler object.
```python
# Source: hand-rolled; LambdaLR multiplies BASE lr by the returned factor
import math
from torch.optim.lr_scheduler import LambdaLR

def build_lr_lambda(warmup_steps: int, max_steps: int, min_ratio: float = 0.1):
    def lr_lambda(step: int) -> float:                 # returns a MULTIPLIER on base lr
        if step < warmup_steps:
            return (step + 1) / max(1, warmup_steps)    # linear 0 -> 1
        if step >= max_steps:
            return min_ratio
        progress = (step - warmup_steps) / max(1, max_steps - warmup_steps)
        cosine = 0.5 * (1.0 + math.cos(math.pi * progress))  # 1 -> 0
        return min_ratio + (1.0 - min_ratio) * cosine        # decay to floor
    return lr_lambda

scheduler = LambdaLR(optimizer, build_lr_lambda(cfg.warmup_steps, cfg.max_steps))
```
`warmup_steps` and `max_steps` come straight from `TrainConfig` (defaults 100 / 5000). `LambdaLR.state_dict()` serializes `last_epoch` (the step counter), which is exactly what `checkpoint.py` saves and restores — resume continues the schedule at the right step. `[CITED: docs.pytorch.org LambdaLR]` `[VERIFIED: TrainConfig L88-93]`

> **Caveat to flag for the planner:** `LambdaLR.state_dict()` cannot pickle a *closure*-based lambda cleanly across processes in older torch; in 2.x it stores `last_epoch` and (best-effort) the lambda. For resume we only need `last_epoch` restored and the *same* lambda rebuilt at construction — which the harness does (it always rebuilds `build_lr_lambda(...)` before `load_checkpoint`). So resume is safe as long as the schedule is reconstructed identically before loading state. `[ASSUMED — verify with a resume test on the real schedule]`

### Anti-Patterns to Avoid
- **Clipping before `unscale_`:** clips scaled gradients → effective clip threshold is `scale`× too large → silently no-ops clipping. Always `unscale_` first.
- **`scheduler.step()` inside the micro-batch loop:** advances LR `grad_accum_steps`× too fast. Step once per optimizer step.
- **Re-seeding on resume:** `seed_everything` is fresh-run-only; calling it on resume rewinds RNG to step 0 and breaks trajectory equality. `load_checkpoint` restores state. `[VERIFIED: seeding.py docstring, checkpoint.py L90-95]`
- **Splitting the corpus mid-document:** breaks the doc-level no-leakage guarantee. Split only on `eos_id` boundaries.
- **Putting `assemble_loss` in the model:** defeats the entire M2 EWC seam (D-03). Loss assembly lives in the loop.
- **Re-implementing device/AMP/bf16 logic in the loop:** `RuntimeConfig` is the single source of truth; the loop calls `runtime.autocast()` and reads `runtime.amp`/`runtime.device`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cross-entropy | Manual log-softmax + gather + NLL | `F.cross_entropy(logits.view(B*T,V), targets.view(B*T))` | Math primitive; numerically stable; nanoGPT-canonical (D-02a). |
| Gradient clipping | Manual norm + rescale loop | `torch.nn.utils.clip_grad_norm_` | Handles param groups, norm types, inf/nan. |
| AMP scaling | Manual loss×scale / grad÷scale | `torch.amp.GradScaler` | Dynamic scale, inf/nan skip, the supported `unscale_` clip path. |
| LR schedule state | A bare `lr_lambda(step)` + manual `param_group['lr']=` | `torch.optim.lr_scheduler.LambdaLR` | `checkpoint.py` requires `scheduler.state_dict()` (D-05) — a function has none. |
| Checkpoint/resume + RNG | New save/load code | Existing `save_checkpoint`/`load_checkpoint` | Already open-dict, RNG-state-restoring, tested (D-05). Do NOT touch it. |
| Restart-safe logging | New CSV writer | Existing `CSVLogger` | Append-only, header-once, flush-per-row, restart-safe (TRAIN-04). |
| Seeding | New seed helper | Existing `seed_everything` | Seeds python/numpy/torch(+cuda), disables cudnn autotuner (ENV-05). |
| Optimizer | Hand-written Adam | `torch.optim.AdamW` | `weight_decay` decoupled correctly; reads `TrainConfig.weight_decay/lr`. |
| Tokenization | Re-encode logic | Frozen `BPETokenizer` via `from_json("artifacts/tokenizer.json")` | Phase-2 deliverable, frozen; encode fixture only, do NOT retrain. |

**Key insight:** Phase 3 writes almost no novel infrastructure — its from-scratch content is the **bigram**, the **`assemble_loss` identity**, the **LR lambda math**, the **doc-level split + `get_batch`**, and the **loop orchestration**. Everything else is *driving* Phase-1/2 primitives. The portfolio "from scratch" claim is satisfied by the model + loop math, not by re-implementing AMP/clipping/checkpointing.

## Runtime State Inventory

> Phase 3 is **greenfield** (new modules + new tests + a new committed fixture). It introduces no rename/refactor of existing runtime state. The only persistent artifacts it *writes* are training outputs, all of which must be `.gitignore`d (already covered).

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — Phase 3 reads the frozen `artifacts/tokenizer.json` (existing) and writes a checkpoint `latest.pt` + a CSV log, both transient training outputs. | Confirm `.gitignore` covers `*.pt`, checkpoints, and `*.csv` logs (Phase 1 said it covers tokens/checkpoints/logs — verify the CSV path/glob is included). |
| Live service config | None — fully offline, no external services. | None. |
| OS-registered state | None — no schedulers, daemons, or registered tasks. | None. |
| Secrets/env vars | None — no new secrets; optional `CUBLAS_WORKSPACE_CONFIG` only under `seed_everything(strict=True)` (off by default). | None. |
| Build artifacts | None new — `model/` and `training/` add importable modules to the already-installed editable package; no reinstall needed (`pip install -e .` picks up new files). | None (editable install already covers new modules). |

**Verification note:** Confirm the training-output paths the harness writes (`latest.pt`, the run CSV) are inside an ignored directory so they never get committed. `[ASSUMED — planner should add an explicit .gitignore check task if not already covered]`

## Common Pitfalls

### Pitfall 1: AMP ordering is unverifiable on CPU if the scaler short-circuits
**What goes wrong:** With `enabled=False` (CPU/fp32), `GradScaler` calls are pass-throughs, so a naive "does it run?" test proves nothing about *ordering*.
**Why it happens:** The whole point of AMP is GPU-only; CI is CPU-only.
**How to avoid:** Make the step a function whose ordering is *observable* — e.g., spy on call order via a wrapped optimizer/scaler or a recorded call-log, OR assert the structural invariant that `clip_grad_norm_` is invoked after `scaler.unscale_`. The cleanest seam (D-07a) is to record the sequence of operations in the loop and assert `["scale_backward"*accum, "unscale", "clip", "step", "update"]`. Pair with a `@pytest.mark.skipif(not torch.cuda.is_available())` smoke test that runs the real fp16 path on GPU (D-07b).
**Warning signs:** A test that only checks the final loss decreased — it cannot catch a clip-before-unscale bug.

### Pitfall 2: `scheduler.step()` in the wrong place under accumulation
**What goes wrong:** Calling `scheduler.step()` per micro-batch advances the LR schedule `grad_accum_steps`× too fast; warmup ends early and cosine decays prematurely.
**Why it happens:** Copy-pasting a non-accumulating loop.
**How to avoid:** `scheduler.step()` fires exactly once per `optimizer.step()` (after `scaler.update()`), outside the micro-batch loop. Add a test asserting LR after N optimizer steps matches the lambda at step N (not N×accum).
**Warning signs:** LR hits its floor far earlier than `max_steps`.

### Pitfall 3: Train/val leakage from windowed sampling near the split boundary
**What goes wrong:** If `get_batch` can draw a window that straddles the train/val boundary, val tokens leak into training.
**Why it happens:** Sampling a random start index `i` then taking `tokens[i:i+block_size+1]` without bounding `i` to `len(split) - block_size - 1`, or splitting a single flat array by index rather than by document.
**How to avoid:** Split into **two separate arrays** (`train_ids`, `val_ids`) on `eos_id` document boundaries; sample windows independently within each. Assert the two arrays share no document and that every val window's tokens come only from val docs. With ≥2 docs (D-06), put ≥1 whole doc in val.
**Warning signs:** Val loss suspiciously tracks train loss from step 0.

### Pitfall 4: Resume reproduces params but not the *logged curve*
**What goes wrong:** The param trajectory matches but the CSV shows a discontinuity because the post-resume run re-logs from step 0 or duplicates a header.
**Why it happens:** Re-opening the logger with a fresh file, or restarting the step counter from 0 instead of `ckpt["step"]`.
**How to avoid:** Resume must (a) read `step` from the checkpoint and continue the loop counter, and (b) re-open the *same* CSV path so `CSVLogger` appends without a duplicate header (already its behavior). The curve-reproducibility test concatenates pre-kill + post-resume CSV rows and asserts they equal an uninterrupted run's rows (within tolerance for the float losses).
**Warning signs:** Two header rows in the CSV; a step counter that resets.

### Pitfall 5: Overfit gate flaky due to LR schedule fighting convergence
**What goes wrong:** With warmup, the first `warmup_steps` have near-zero LR, so a short overfit budget never converges.
**Why it happens:** Reusing the full-run schedule (warmup 100, max 5000) for a tiny overfit test.
**How to avoid:** The overfit test should use a *small* `TrainConfig` (e.g., `warmup_steps=0` or a tiny value, `max_steps` ~ a few hundred, higher `lr`) and a single fixed batch reused every step. Assert final loss below a small threshold (bigram on one batch should drive CE well below its uniform-init value `ln(8192)≈9.0` — target e.g. `< 0.5` or even near 0 given the lookup table can memorize a fixed batch). Deterministic via `seed_everything`.
**Warning signs:** Test passes locally but flakes in CI — usually an unseeded data draw or too-tight a threshold.

### Pitfall 6: Re-encoding the fixture nondeterministically / retraining the tokenizer
**What goes wrong:** Accidentally calling `BPETokenizer().train(...)` instead of loading the frozen artifact, or encoding with `allowed_special` such that `<|endoftext|>` is byte-split.
**Why it happens:** Forgetting the tokenizer is a frozen Phase-2 deliverable.
**How to avoid:** Load via `from_json("artifacts/tokenizer.json")`; encode the fixture with `allowed_special="all"` so the EOS literal maps atomically to `eos_id=8184` (the tokenizer already does longest-first atomic special handling). Assert the encoded array contains `8184` at the document boundaries. `[VERIFIED: bpe.py encode L151-185]`

## Code Examples

### Doc-level split with no leakage (from a committed fixture)
```python
# Source: nanoGPT data idiom + frozen Phase-2 tokenizer; D-06 doc-level split
import numpy as np
from personacore.tokenizer import from_json

def load_split(fixture_path, eos_id=8184, val_docs=1):
    tok = from_json("artifacts/tokenizer.json")          # FROZEN — do not retrain
    text = open(fixture_path, encoding="utf-8").read()
    ids = tok.encode(text, allowed_special="all")         # eos -> atomic 8184
    # split into documents on the eos boundary (keep eos as each doc's terminator)
    docs, cur = [], []
    for t in ids:
        cur.append(t)
        if t == eos_id:
            docs.append(cur); cur = []
    if cur:
        docs.append(cur)
    assert len(docs) >= 2, "fixture must contain >= 2 documents (D-06)"
    val = docs[-val_docs:]                                # whole docs to val (no straddle)
    train = docs[:-val_docs]
    train_ids = np.array([t for d in train for t in d], dtype=np.uint16)
    val_ids   = np.array([t for d in val   for t in d], dtype=np.uint16)
    return train_ids, val_ids
```

### `get_batch` random contiguous window sampler
```python
# Source: nanoGPT get_batch
import numpy as np, torch

def get_batch(arr, batch_size, block_size, device):
    ix = np.random.randint(0, len(arr) - block_size - 1, size=batch_size)  # bounded -> no overrun
    x = torch.stack([torch.from_numpy(arr[i:i+block_size].astype(np.int64)) for i in ix])
    y = torch.stack([torch.from_numpy(arr[i+1:i+1+block_size].astype(np.int64)) for i in ix])
    return x.to(device), y.to(device)
```
Note: cast to `int64` for `nn.Embedding`/`cross_entropy` index dtype; the storage stays `uint16`.

### `assemble_loss` seam (identity in M1)
```python
# Source: D-04 — dead-simple, fully unit-testable now
def assemble_loss(base_loss, extra_penalties=()):
    """base + sum(extra). M1 passes () -> returns base unchanged (identity)."""
    total = base_loss
    for p in extra_penalties:        # each p is a precomputed scalar tensor
        total = total + p
    return total
```
Test (D-04a): `assemble_loss(x, ())` equals `x` (identity); `assemble_loss(x, (p,))` equals `x + p` for a dummy scalar tensor `p`. M2 EWC will pass `(fisher_penalty,)` with zero changes here.

### Estimate validation loss periodically
```python
# Source: nanoGPT estimate_loss; eval mode + no_grad
@torch.no_grad()
def estimate_loss(model, val_arr, cfg, device, iters=20):
    model.eval()
    losses = []
    for _ in range(iters):
        xb, yb = get_batch(val_arr, cfg.batch_size, cfg.block_size, device)
        _, loss = model(xb, yb)
        losses.append(loss.item())
    model.train()
    return sum(losses) / len(losses)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `torch.cuda.amp.GradScaler` / `torch.cuda.amp.autocast` | `torch.amp.GradScaler(device=...)` / `torch.autocast(device_type=...)` | torch 2.x (the `torch.cuda.amp.*` API is deprecated) | Use the device-generic `torch.amp` API. `RuntimeConfig.autocast()` already uses `torch.autocast` correctly. `[CITED: docs.pytorch.org/docs/stable/amp.html]` |
| `optimizer.zero_grad()` | `optimizer.zero_grad(set_to_none=True)` | default flipped to `True` in torch 2.0 | Faster + correct; harmless to pass explicitly. `[ASSUMED]` |
| `weights_only=False` default in `torch.load` | `weights_only=True` default (torch ≥2.6) | torch 2.6 | The resume checkpoint MUST pass `weights_only=False` (it carries pickled RNG/optimizer) — `load_checkpoint` already does. `[VERIFIED: checkpoint.py L83]` |

**Deprecated/outdated:**
- `torch.cuda.amp.*` — use `torch.amp.*`. The repo's `RuntimeConfig.autocast()` is already on the modern API.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `LambdaLR` resume is safe as long as the lambda is reconstructed identically before `load_state_dict` (only `last_epoch` must restore) | LR Schedule Pattern 4 / Alternatives | LOW — mitigated by a resume test on the real schedule; if wrong, switch to storing/restoring step explicitly and computing LR manually after restore. |
| A2 | Overfit threshold (e.g. `< 0.5` CE on one fixed batch within a few hundred steps) is achievable for a `(V,V)` bigram | Overfit Gate / Pitfall 5 | LOW — a lookup table can memorize a fixed batch trivially; planner should let the executor calibrate the exact threshold/budget empirically and pin it. |
| A3 | `F.cross_entropy` inside `forward` satisfies the from-scratch ethos (treated as a math primitive like `sdpa`) | Bigram Model / Don't Hand-Roll | LOW — consistent with CLAUDE.md allowing `sdpa`; if the portfolio narrative wants manual CE, add a tested manual variant (not required). |
| A4 | In-memory numpy `uint16` array (vs tiny on-disk `.bin`) is acceptable for D-06 | Data Path / Alternatives | LOW — D-06 explicitly allows "in-memory / tiny on-disk"; either satisfies the requirement. |
| A5 | `.gitignore` already covers the CSV training-log glob | Runtime State Inventory | LOW — Phase 1 said tokens/checkpoints/logs are ignored; planner should add an explicit verify task. |
| A6 | `zero_grad(set_to_none=True)` is the current default and the recommended form | State of the Art | NEGLIGIBLE — cosmetic. |

## Open Questions

1. **CSV `fieldnames` schema** — STACK.md suggests `step,train_loss,val_loss,lr,tokens,wall_clock`. CONTEXT.md says fieldnames are "the planner's call." 
   - What we know: `CSVLogger(path, fieldnames)` takes any field list; the curve must be reproducible from the log.
   - What's unclear: exact column set (e.g., whether to log `grad_norm`).
   - Recommendation: use `step,train_loss,val_loss,lr,tokens,wall_clock`; the reproducibility test only needs `step` + the losses.

2. **Where the minimal `sample()` lives** — `model/bigram.py` (a `@torch.no_grad() generate`-lite method) or `training/loop.py`.
   - Recommendation: a tiny free function in `training/loop.py` (or a thin `sample()` helper) so the model stays pure and Phase-6's full `generate()` can supersede it without a model rewrite. D-11 only requires "see output."

3. **Overfit test config** — exact `(lr, max_steps, warmup_steps, threshold)` for a fast, non-flaky CPU gate.
   - Recommendation: planner specifies a dedicated small `TrainConfig` (warmup 0, ~200-500 steps, lr ~1e-2..1e-1) and lets the executor pin the threshold from an observed run (A2).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `torch` (CPU) | entire harness + tests | ✓ (project dep) | `2.7.*` local / Kaggle pre-installed | — |
| `numpy` | token array / `get_batch` | ✓ (project dep) | `>=1.26,<3` | — |
| `pytest` | seam tests | ✓ (`[dev]`) | `~=9.0` | — |
| frozen tokenizer artifact | fixture encode | ✓ present | `artifacts/tokenizer.json` | — (Phase-2 deliverable) |
| CUDA / P100 GPU | AMP fp16 smoke test only (D-07b) | ✗ (laptop CPU) | — | `skipif(not cuda)` — test is GPU-conditional; CPU path covers ordering |
| `matplotlib` | plot helper IF shipped now | likely ✓ | 3.9+ | Defer plotting to Phase 8 `demo.ipynb`; the curve-reproducibility test reads CSV directly (no matplotlib needed) |

**Missing dependencies with no fallback:** None.
**Missing dependencies with fallback:** GPU — the AMP fp16 path is verified on CPU via *ordering* assertions (D-07a) and the actual-fp16 run is a `skipif`-guarded smoke test (D-07b). No GPU is required for the phase to pass CI.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest `~=9.0` (`pyproject.toml [project.optional-dependencies] dev`) |
| Config file | `pyproject.toml` → `[tool.pytest.ini_options]` (`testpaths=["tests"]`, `pythonpath=["."]`) |
| Quick run command | `pytest tests/test_<seam>.py -x -q` |
| Full suite command | `make test` (CPU-only; equivalent to `pytest`) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MODEL-01 | `forward(idx,None)->(logits,None)`; `forward(idx,targets)->(logits,loss)`; logits shape `(B,T,V)`; CE flatten correct | unit | `pytest tests/test_bigram_model.py -x` | ❌ Wave 0 |
| TRAIN-01 | AdamW step runs; grad-accum N micro-batches == 1 big batch (within tol); grad clip applied | unit | `pytest tests/test_train_loop.py -x` | ❌ Wave 0 |
| TRAIN-01 | warmup ramps 0→base over `warmup_steps`; cosine decays to floor; `state_dict()` round-trips | unit | `pytest tests/test_lr_schedule.py -x` | ❌ Wave 0 |
| TRAIN-02 | AMP step ORDERING: `unscale_` before `clip` before `step` before `update`; one `unscale_`/opt-step (CPU) | unit | `pytest tests/test_train_loop.py::test_amp_ordering -x` | ❌ Wave 0 |
| TRAIN-02 | real fp16 AMP path runs without inf/nan | smoke (GPU) | `pytest tests/test_train_loop.py::test_amp_fp16_smoke -x` (`skipif(not cuda)`) | ❌ Wave 0 |
| TRAIN-03 | doc-level split → disjoint train/val docs; `get_batch` shapes/dtype/in-bounds; NO leakage | unit | `pytest tests/test_data_split.py -x` | ❌ Wave 0 |
| TRAIN-04 | CSV survives restart (append, single header); concatenated pre/post-resume curve == uninterrupted run | unit | `pytest tests/test_resume_curve.py -x` | ❌ Wave 0 |
| TRAIN-05 | overfit one fixed batch → final loss < threshold; deterministic under seed | unit | `pytest tests/test_overfit_batch.py -x` | ❌ Wave 0 |
| TRAIN-06 | `assemble_loss(x,())==x` (identity); `assemble_loss(x,(p,))==x+p` (additive) | unit | `pytest tests/test_assemble_loss.py -x` | ❌ Wave 0 |
| TRAIN-06 | open-dict checkpoint round-trips `**extra` | unit | `pytest tests/test_checkpoint.py::test_open_dict_extensible` | ✅ (exists) |
| TRAIN-04/06 | bigram save→kill→resume reproduces param + loss trajectory within 1e-6 | unit | `pytest tests/test_resume_curve.py::test_resume_identical_trajectory_bigram` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_<seam_just_touched>.py -x -q` (each seam test is CPU-fast, < a few seconds).
- **Per wave merge:** `make test` (full CPU suite, including the inherited Phase-1/2 tests).
- **Phase gate:** Full suite green + the four hard-correctness gates demonstrably pass — overfit convergence (TRAIN-05), resume curve reproducibility (TRAIN-04), no train/val leakage (TRAIN-03), AMP ordering (TRAIN-02) — before `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `tests/fixtures/bigram_corpus.txt` — ≥2 TinyStories-style docs separated by `<|endoftext|>` (the committed D-06 fixture).
- [ ] `tests/test_bigram_model.py` — covers MODEL-01 (forward contract, shapes, CE flatten).
- [ ] `tests/test_assemble_loss.py` — covers TRAIN-06 seam (identity + additive, D-04a).
- [ ] `tests/test_lr_schedule.py` — covers TRAIN-01 schedule (warmup/cosine/state_dict).
- [ ] `tests/test_data_split.py` — covers TRAIN-03 (doc split, no leakage, `get_batch`).
- [ ] `tests/test_train_loop.py` — covers TRAIN-01/02 (grad accum equivalence, AMP ordering, GPU smoke).
- [ ] `tests/test_overfit_batch.py` — covers TRAIN-05 (overfit gate).
- [ ] `tests/test_resume_curve.py` — covers TRAIN-04/06 (resume trajectory + curve reproducibility) — extend the existing `test_checkpoint.py` pattern to the bigram + LambdaLR + CSV.
- [ ] Register a `cuda`/`gpu` pytest marker OR use inline `@pytest.mark.skipif(not torch.cuda.is_available())` for the AMP fp16 smoke test (no marker currently registered in `pyproject.toml`).
- Framework install: none — `pytest~=9.0` already in `[dev]`.

## Security Domain

> `security_enforcement` is not set in `.planning/config.json`; the project is fully offline, zero-budget, on-device, with no network/auth/storage surface in Phase 3. The relevant security facts are inherited and already handled.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth surface (offline, on-device). |
| V3 Session Management | no | No sessions. |
| V4 Access Control | no | No multi-user surface. |
| V5 Input Validation | minimal | Fixture is a committed trusted file; tokenizer `decode` is strict UTF-8 (raises, no silent replacement). |
| V6 Cryptography | no | None. |
| V14 Config / Supply Chain | yes | Resume checkpoint loads with `weights_only=False` (pickle) — already documented TRUSTED-ONLY (own files); no new deps introduced. |

### Known Threat Patterns for this stack
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Untrusted pickle load via `torch.load(weights_only=False)` | Tampering / RCE | Already mitigated: load only own checkpoints; slim INFERENCE checkpoint (Phase 8) uses `weights_only=True`. No change in Phase 3. `[VERIFIED: checkpoint.py L16-21,83]` |
| Slopsquatted dependency | Supply chain | None introduced this phase; all deps pre-vetted (Phases 1-2). |

## Sources

### Primary (HIGH confidence)
- Repo code (`src/personacore/config.py`, `checkpoint.py`, `logging.py`, `seeding.py`, `tokenizer/bpe.py`, `tokenizer/__init__.py`, `tests/test_checkpoint.py`, `tests/conftest.py`, `pyproject.toml`) — actual signatures/contracts cited inline `[VERIFIED: repo grep]`.
- `.planning/phases/03-bigram-baseline-training-harness/03-CONTEXT.md` — locked decisions D-01..D-11.
- `.planning/REQUIREMENTS.md` / `.planning/ROADMAP.md` — MODEL-01, TRAIN-01..06 acceptance + Phase-3 success criteria.
- `CLAUDE.md` / `.planning/research/STACK.md` — P100/AMP discipline, from-scratch ethos, offline logging.
- PyTorch AMP examples — https://docs.pytorch.org/docs/stable/notes/amp_examples.html (gradient accumulation + clipping ordering).
- PyTorch AMP API — https://docs.pytorch.org/docs/stable/amp.html (`torch.amp.GradScaler`, `unscale_`).
- PyTorch `LambdaLR` — https://docs.pytorch.org/docs/stable/generated/torch.optim.lr_scheduler.LambdaLR.html (`state_dict()` resumability).

### Secondary (MEDIUM confidence)
- nanoGPT / makemore (Karpathy) — conceptual reference for the bigram, `get_batch`, `(logits,loss)` forward, overfit-one-batch gate (re-implemented by hand, not vendored).

### Tertiary (LOW confidence)
- None requiring validation beyond the Assumptions Log (A1-A6).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new deps; everything is `torch`/`numpy`/internal, verified in repo.
- Architecture: HIGH — grounded in actual `config.py`/`checkpoint.py`/`logging.py` contracts and the existing kill-and-resume test.
- AMP discipline: HIGH — ordering cited from official PyTorch AMP examples; CPU-test strategy follows D-07.
- Pitfalls: HIGH — derived from the documented PyTorch ordering rules + the repo's own RNG-state-restore design.
- LambdaLR resume nuance: MEDIUM (A1) — flagged for a concrete resume test on the real schedule.

**Research date:** 2026-06-04
**Valid until:** 2026-07-04 (stable; the only moving part is PyTorch AMP API surface, which is settled in 2.x)
