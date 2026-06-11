# Architecture Research — v2.0 Weight-Based Memory

**Domain:** From-scratch LoRA + EWC continual learning on an existing from-scratch GPT (PersonaCore v1.0 base, 13.9M params, MPS/CPU)
**Researched:** 2026-06-11
**Confidence:** HIGH for integration points (verified line-by-line against the shipped v1.0 code), HIGH for LoRA/EWC mechanics (paper-canonical patterns), MEDIUM for dialog-corpus acquisition details (raw downloads verified to exist; exact parsing deferred to implementation)

## Executive Summary

v2.0 is **additive, not a rewrite** — that was the entire point of the v1.0 seam discipline, and the seams are real. Verified against the shipped code:

1. **LoRA seam** — `model/gpt.py` exposes six named `nn.Linear` projections per block (`q_proj/k_proj/v_proj/c_proj/fc_in/fc_out`), pinned by `tests/test_gpt_lora_seam.py`. LoRA wraps these **post-construction, post-load** via parent-module `setattr` injection. `gpt.py` is **not edited at all** in v2.0.
2. **EWC seam** — `training/loss.py::assemble_loss(base, extra_penalties=())` exists, but note: `training/loop.py:138` currently hardcodes `assemble_loss(base_loss, ())`. EWC therefore needs **one minimal additive change to `loop.py`** (an optional `penalty_fn=None` kwarg threaded into `_optimizer_step`). `assemble_loss` itself and its D-04 contract (precomputed scalar tensors, no callables) are consumed verbatim.
3. **Checkpoint seam** — `checkpoint.py::save_checkpoint(**extra)` accepts `fisher=` / `theta_star=` / `lora_config=` today with zero format change (the docstring reserves exactly this). The **slim `weights_only=True` artifact schema is untouched**: personalized weights ship as a *merged* plain-GPT `state_dict`, so `load_slim`, the demo, and the dead-id mask all work verbatim.
4. **Tokenizer budget** — the chat-role specials are already reserved and top-pinned: `<|user|>`=8185, `<|assistant|>`=8186, `<|system|>`=8187, `<|pad|>`=8188 (`tokenizer/special.py`). Conversational formatting needs **no tokenizer change** and no new ids. Role ids 8185–8187 go "live" in stage 2; they are already in `special_tokens`, so `undecodable_ids_mask` already treats them as decodable — the `forbid_ids` mask needs zero changes.
5. **Loss masking** — `GPT.forward`'s LOCKED tail is `F.cross_entropy(logits.view(B*T,V), targets.view(B*T))`, whose default `ignore_index=-100` means assistant-only loss masking is done **entirely in the data path** (set masked target positions to −100 at batch assembly). The LOCKED `forward(idx, targets=None) -> (logits, loss)` contract is respected with zero model edits.

New code lands in two new packages (`lora/`, `continual/`), one new data-prep script family, additive kwargs on `train()` and `generate()`, and demo/viz scripts. Everything else is consumed as-is.

## System Overview

```
                         v1.0 (UNTOUCHED)                      v2.0 (NEW / MODIFIED)
┌──────────────────────────────────────────────┐  ┌─────────────────────────────────────────┐
│ model/gpt.py        forward(idx,targets)     │  │ lora/layer.py      LoRALinear wrapper   │
│   six named nn.Linear per block  ◄───────────┼──┼ lora/inject.py     inject/merge/freeze  │
│                                              │  │                                         │
│ training/loss.py    assemble_loss(base, ())  │  │ continual/fisher.py  estimate_fisher()  │
│ training/loop.py    train(), _optimizer_step ◄──┼ continual/ewc.py     EWCPenalty(...)    │
│   [+penalty_fn, +extra_val_bins — ADDITIVE]  │  │                                         │
│                                              │  │ scripts/prepare_dialog_corpus.py        │
│ training/data.py    get_batch_memmap         ◄──┼   DailyDialog+PersonaChat → bins+masks  │
│   [+masked-batch variant — ADDITIVE]         │  │ scripts/finetune_dialog.py (stage 2)    │
│                                              │  │ scripts/run_ab_forgetting.py (A/B)      │
│ checkpoint.py       save_checkpoint(**extra) ◄──┼   fisher / theta_star / lora_config     │
│   open dict — NO format change               │  │                                         │
│ checkpoint.py       export_slim / load_slim  ◄──┼ merged plain-GPT weights only (LOCKED)  │
│                                              │  │                                         │
│ generation/core.py  generate(...)            │  │ scripts/personalize_demo.py             │
│   [+stop_ids — ADDITIVE]                     │  │   gr.Blocks Teach / Chat / Reset        │
│ generation/text.py  undecodable_ids_mask     │  │                                         │
│                                              │  │ scripts/make_m2_figures.py              │
│ logging.py CSVLogger │ evaluation/perplexity ◄──┼   forgetting curves + Δ-weight heatmaps │
└──────────────────────────────────────────────┘  └─────────────────────────────────────────┘
```

### Task sequence the architecture serves

- **Task 1 (done, v1.0):** TinyStories pretrain → `best.pt` (the EWC anchor θ*).
- **Stage 2 (v2.0):** conversational fine-tune on DailyDialog + PersonaChat — **full-model fine-tune with EWC** anchored at `best.pt` (Fisher estimated on TinyStories). The A/B no-forgetting demo runs this twice: λ=0 (naive) vs λ>0 (EWC).
- **Stage 3 (v2.0):** personalization — **LoRA** adapters on the conversational base, trained on a tiny user-facts set (teach-then-recall demo). LoRA is the per-user, deletable, mergeable memory mechanism.

**Why this split (opinionated):** shifting register from child stories to dialog is a whole-model change — r=8 LoRA capacity is the wrong tool and would muddy the EWC story; conversely, personalization must be fast (~minutes on-device), small, and *deletable* (privacy narrative: deleting memory = deleting an adapter), which is exactly LoRA. EWC-on-LoRA-params (θ* = zero-init adapters) degenerates to Fisher-weighted L2-to-zero — possible as a stretch experiment, not the headline.

## Component Responsibilities

| Component | Status | Responsibility | Key integration fact |
|-----------|--------|----------------|----------------------|
| `src/personacore/lora/layer.py` | **NEW** | `LoRALinear(nn.Module)`: composition wrapper holding the frozen base `nn.Linear` + `lora_A` (r×in, small-normal/Kaiming init) + `lora_B` (out×r, **zeros init**), `forward = base(x) + (alpha/r)·(x @ Aᵀ @ Bᵀ)` | B=0 ⇒ injected model is bit-identical to base at step 0 (the unit-test gate) |
| `src/personacore/lora/inject.py` | **NEW** | `inject_lora(model, targets, r, alpha)` (parent-`setattr` walk over `model.blocks[i].attn/.mlp`), `merge_lora(model)` (fold ΔW=scale·B@A into base weight, swap plain `nn.Linear` back), `mark_only_lora_trainable(model)`, `lora_state_dict(model)` (key-filtered adapter-only dict) | Injection happens **after** `best.pt` (or stage-2 ckpt) weights are loaded into a vanilla `GPT` — base keys match verbatim, no `strict=False` gymnastics |
| `src/personacore/continual/fisher.py` | **NEW** | `estimate_fisher(model, bin_path, n_batches, batch_size, block_size, device)` → `{name: tensor}` diagonal empirical Fisher: eval-mode, seeded window draws from `train.bin`, accumulate squared grads of CE, average; trainable params only | Pure function of existing memmap path + model; run **before** training, RNG-forked so it never touches the training trajectory |
| `src/personacore/continual/ewc.py` | **NEW** | `EWCPenalty(fisher, theta_star, lam)` — callable `(model) -> scalar tensor`: `(λ/2)·Σ F_i(θ_i−θ*_i)²` over named trainable params | This is the `penalty_fn` handed to `train()`; deterministic in params ⇒ resume-equality contract survives |
| `training/loop.py` | **MODIFIED (additive)** | + `penalty_fn=None` (per micro-batch: `assemble_loss(base_loss, (penalty_fn(model),))` — D-04 still receives precomputed scalars); + `extra_val_bins=None` (dict name→bin path → extra `val_<name>` CSV columns via `estimate_loss`, which already RNG-snapshots itself); CSV fieldnames become per-run, derived | Defaults reproduce v1.0 behavior bit-for-bit → all 137 existing tests stay green |
| `training/data.py` | **MODIFIED (additive)** | + `get_batch_memmap_masked(bin_path, mask_path, ...)`: draws aligned windows from token bin + uint8 mask bin, builds shifted `y`, sets `y[mask==0] = -100` | `F.cross_entropy` default `ignore_index=-100` ⇒ loss masking with **zero model change** (LOCKED forward respected) |
| `checkpoint.py` | **UNCHANGED** | Stage-2/3 resume checkpoints carry `fisher=`, `theta_star=`, `ewc_lambda=`, `fisher_meta=`, `lora_config=` via the existing `**extra` | Docstring line 75 reserves exactly this; `load_checkpoint` returns the full dict so callers read the extra keys |
| `checkpoint.py::export_slim/load_slim` | **UNCHANGED** | Ship-path for personalized weights = `merge_lora` → plain GPT `state_dict` → existing slim schema | LOCKED `weights_only=True` contract holds: merged weights are ordinary tensors under the v1.0 keys; demo loads them with zero changes. Optional extra artifact: `adapter.pt` (lora-only tensors + primitives — also `weights_only=True`-safe) |
| `generation/core.py` | **MODIFIED (additive)** | + `stop_ids=None` kwarg (default `{eos_id}`): stop-without-yield on any id in the set | Chat inference must stop when the model starts a `<|user|>` turn; `generate()` is NOT on the LOCKED list — only `forward`, RNG-resume, and slim `weights_only=True` are |
| `scripts/prepare_dialog_corpus.py` | **NEW** | Run-once (mirrors `encode_corpus.py`): raw DailyDialog zip + `personachat_self_original.json` → role-token-formatted docs → frozen tokenizer encode (`allowed_special="all"`) → `dialog_train.bin`/`dialog_val.bin` (uint16) + `dialog_train_mask.bin`/`dialog_val_mask.bin` (uint8, 1=assistant span) | Frozen tokenizer, never retrained (locked milestone decision); doc-level train/val split on `<|endoftext|>` like v1.0 |
| `scripts/finetune_dialog.py` | **NEW** | Stage-2 driver: load `best.pt` into vanilla GPT → `estimate_fisher` (or load cached) → build `EWCPenalty` → `train(model=..., train_bin=dialog bins, penalty_fn=..., extra_val_bins={"tinystories": val.bin})` → conversational-base ckpt | Reuses `train()` end-to-end: warmup/cosine, grad-accum, kill+resume, best.pt tracking all inherited |
| `scripts/run_ab_forgetting.py` | **NEW** | Two-arm cohort (λ=0 vs λ>0), same seed/budget, mirrors `run_ablations.py` precedent (calibrated short budget); writes one CSV per arm | Forgetting curve = `val_tinystories` column over steps, per arm; endpoint headline = deterministic `evaluation/perplexity()` on both tasks |
| `scripts/personalize_demo.py` | **NEW** | `gr.Blocks` Teach/Chat/Reset: Teach = facts textbox → templated+paraphrased mini-corpus → `inject_lora` → short `train()` on-device → live; Chat = `generate_text_cumulative` with `forbid_ids` + `stop_ids`; Reset = drop adapter (instant forget) | Clean-room recall: fresh chat, **empty context** (the v1.0 demo already never concatenates history — the proof posture is inherited) |
| `scripts/make_m2_figures.py` | **NEW** | Committed PNGs: forgetting curves (CSV → matplotlib) + weight-delta heatmaps (checkpoint pair → per-(layer, projection) mean abs-ΔW grid, n_layer×6; embedding-row delta strip for role ids; LoRA arms compute ΔW = scale·B@A exactly) | Reads slim/full checkpoints and run CSVs only — no training dependency; outputs to `results/`/`docs/assets/` (committed deliverables) |

## Recommended Project Structure (v2.0 additions only)

```
src/personacore/
├── lora/                      # NEW package — the from-scratch LoRA deliverable
│   ├── __init__.py
│   ├── layer.py               # LoRALinear (composition wrapper; ~60 lines, fully unit-testable)
│   └── inject.py              # inject_lora / merge_lora / mark_only_lora_trainable / lora_state_dict
├── continual/                 # NEW package — the from-scratch EWC deliverable
│   ├── __init__.py
│   ├── fisher.py              # estimate_fisher (diagonal empirical Fisher over memmap windows)
│   └── ewc.py                 # EWCPenalty: (λ/2)·Σ F(θ−θ*)² → scalar tensor
├── training/
│   ├── loop.py                # MODIFIED: +penalty_fn, +extra_val_bins (additive, default-off)
│   └── data.py                # MODIFIED: +get_batch_memmap_masked (token bin + uint8 mask bin)
├── generation/
│   └── core.py                # MODIFIED: +stop_ids (additive, default {eos_id})
scripts/
├── prepare_dialog_corpus.py   # NEW: raw dialog data → bins + mask bins (run-once)
├── finetune_dialog.py         # NEW: stage-2 EWC fine-tune driver (no-CLI, _REPO_ROOT constants)
├── run_ab_forgetting.py       # NEW: λ=0 vs λ>0 two-arm experiment
├── personalize_demo.py        # NEW: teach-then-recall Gradio Blocks demo
└── make_m2_figures.py         # NEW: forgetting curves + weight-delta heatmaps (committed PNGs)
tests/
├── test_lora_layer.py         # B=0 identity; grad flows ONLY through A/B; scaling math
├── test_lora_inject.py        # six projections wrapped per block; base keys load verbatim pre-injection
├── test_lora_merge.py         # merged model ≡ adapted model logits (atol); slim export round-trip
├── test_fisher.py             # known-gradient oracle on a tiny model; non-negativity; determinism
├── test_ewc_penalty.py        # quadratic-form oracle; zero at θ=θ*; λ scaling
├── test_loop_penalty_fn.py    # penalty_fn=None ≡ v1.0 trajectory; grad-accum penalty counted exactly once/step
├── test_masked_batch.py       # -100 placement; CE ignores masked positions; window alignment token↔mask
├── test_dialog_format.py      # role-token rendering; atomic special encode; doc-split no-leakage
└── test_stop_ids.py           # stop-without-yield on any stop id; default ≡ v1.0 EOS behavior
```

### Structure rationale

- **`lora/` and `continual/` as separate top-level packages**, not inside `model/` or `training/`: these are the two headline from-scratch deliverables of the milestone — the portfolio reader should find each as a small, self-contained, paper-traceable module. Neither imports the other; `lora/` imports nothing from `training/` (it operates on any `nn.Module` with named Linears), `continual/` imports only the data path.
- **No edits to `model/gpt.py`** — the v1.0-verified model file stays byte-identical. The LoRA seam test (`test_gpt_lora_seam.py`) constructs a vanilla `GPT` and stays green; injection is strictly opt-in and post-construction.
- **Scripts remain thin no-CLI entries** (`_REPO_ROOT` constants, `main()`, no argparse) — the established D-04 pattern from `encode_corpus.py`/`pretrain_tinystories.py`/`run_ablations.py`.

## Architectural Patterns

### Pattern 1: Wrapper-module injection (NOT monkey-patching, NOT `nn.Linear` subclass)

**What:** `LoRALinear` is a plain `nn.Module` that *owns* the frozen base `nn.Linear` (composition). `inject_lora` walks `model.named_modules()`, finds the six target names per block, and `setattr`s the wrapper onto the parent (`block.attn.q_proj = LoRALinear(block.attn.q_proj, r, alpha)`).

**Why this over the alternatives:**
- *Monkey-patching `forward`*: invisible in `state_dict`/`repr`, untestable as a unit, breaks the "from-scratch legibility" portfolio bar. Rejected.
- *`nn.Linear` subclass (loralib-style)*: preserves `q_proj.weight` state-dict keys, but hides the LoRA math behind inheritance and requires re-constructing modules with copied weights. The key-stability advantage is moot because injection happens **after** loading base weights (see load order below). Rejected — composition reads better and the explicit `forward` *is* the deliverable.
- *Wrapper (chosen)*: explicit math, trivially unit-testable (B=0 identity gate; grad-isolation gate), and `merge_lora` is the clean inverse (fold ΔW, `setattr` the plain Linear back).

**Load-order discipline (load-bearing):**
```python
model = GPT(ModelConfig(**ckpt["model_config"]))     # vanilla — keys match best.pt verbatim
model.load_state_dict(ckpt["model"])                 # base weights in, zero key gymnastics
inject_lora(model, targets=SIX_PROJECTIONS, r=8, alpha=16)   # AFTER load
mark_only_lora_trainable(model)                      # requires_grad_(False) then enable lora_A/B
```
Wrapping before loading breaks every key (`q_proj.weight` → `q_proj.base.weight`) — the #1 foreseeable integration bug; pin it with a test.

**LoRA scope:** the six per-block projections only. `wte`/`lm_head` are excluded — they share one tied tensor (`data_ptr`-pinned in v1.0 tests); adapting either would break tying semantics or untie silently. Tying is untouched by injection.

**Checkpoint consequences (explicit):**
- *Resume checkpoint (full, trusted, `weights_only=False`)*: saved from the **adapted** model — keys carry the `.base.` infix; `lora_config={r, alpha, targets}` rides in `**extra`. Resume = rebuild vanilla GPT → `inject_lora` from `lora_config` → `load_checkpoint`. Open-dict format unchanged.
- *Slim ship artifact (LOCKED `weights_only=True`)*: **always merged**. `merge_lora` restores verbatim v1.0 keys, then the existing `export_slim`/`load_slim` path runs unchanged. The "memory lives in the weights" claim is *strongest* here: the shipped file is an ordinary dense `state_dict` with the user's facts baked in — no adapter sidecar at inference.
- *Optional `adapter.pt`*: `lora_state_dict(model)` + `lora_config` (tensors + primitives only → `weights_only=True`-safe). ~332K params at r=8 (≈1.3 MB fp32, ~2.4% of model) — the "your memory is a 1.3 MB file you can delete" narrative artifact.

**Freeze discipline:** existing `train()` builds `AdamW(model.parameters())` — safe as-is: frozen params never receive grads, and AdamW and `clip_grad_norm_` both skip `grad is None` params. No loop change needed for LoRA. Set `TrainConfig.weight_decay=0.0` for adapter runs (decaying A/B fights the low-rank update; standard practice).

### Pattern 2: EWC as a `penalty_fn` computed in the loop, consumed by `assemble_loss`

**What:** `EWCPenalty` is constructed **once** per run (Fisher + θ* + λ), then called per micro-batch inside `_optimizer_step`:

```python
# loop.py — the ONLY semantic change to the v1.0 loop:
with runtime.autocast():
    _, base_loss = model(xb, yb)
    penalties = (penalty_fn(model),) if penalty_fn is not None else ()
    total = assemble_loss(base_loss, penalties)      # D-04: still precomputed scalars
    loss = total / accum
```

**Why here:** the v1.0 seam put loss *assembly* in `training/`, never the model (D-03) — but `loop.py:138` hardcodes `()`. The honest integration is one optional kwarg with default `None` ⇒ identity ⇒ v1.0 trajectory bit-identical (testable). D-04's "no callbacks into `assemble_loss`" is preserved: the loop computes the scalar, `assemble_loss` only sums.

**Grad-accumulation correctness:** the penalty is added per micro-batch and divided by `accum` along with the base loss → exactly **one** full penalty contribution per optimizer step. Pin with a test (penalty gradient counted once, not `accum` times).

**Fisher estimation:** diagonal empirical Fisher — eval mode (dropout already 0.0), seeded draws of N≈200–500 windows (batch 1–8) from TinyStories `train.bin` via the existing memmap path, per batch: `zero_grad → forward → CE → backward → accumulate p.grad²`, average over batches; trainable params only; run inside `torch.random.fork_rng` (or before `train()` starts) so the training RNG trajectory is untouched. Document honestly that ground-truth-target empirical Fisher is the standard practical approximation (vs sampling y from the model).

**Storage:** `save_checkpoint(..., fisher=fisher, theta_star=theta_star, ewc_lambda=lam, fisher_meta={"source": "train.bin", "n_batches": N, "seed": s, "anchor_sha": ...})`. Size: full-model fisher + θ* ≈ 2×55.6 MB fp32 on top of the ~159 MB full checkpoint — fine on local disk, gitignored. θ* duplicates `best.pt`'s weights *by value* deliberately: the resume checkpoint must stay self-contained (no second-file dependency), matching the v1.0 single-source-of-truth posture. Cache the Fisher in its own file (e.g. `checkpoints/fisher_tinystories.pt`) so the A/B's two arms and any re-runs share one estimation pass.

### Pattern 3: Loss masking in the data path via `ignore_index=-100` (zero model change)

**What:** the dialog prep script emits **two aligned bins per split**: `dialog_train.bin` (uint16 token ids) and `dialog_train_mask.bin` (uint8, 1 = position belongs to an assistant span, including the turn's terminator). `get_batch_memmap_masked` draws the same random contiguous windows as `get_batch_memmap` from both files, builds the shifted target `y`, then `y[mask_shifted == 0] = -100`.

**Why:** `GPT.forward`'s LOCKED tail calls `F.cross_entropy(..., targets.view(B*T))` with the default `ignore_index=-100` — masked positions contribute zero loss and zero gradient with **no model edit**. uint16 can't hold −100, hence the parallel uint8 mask bin rather than baking sentinels into the token stream.

**Turn formatting (uses only already-reserved ids):**
```
<|user|> utterance <|assistant|> utterance <|user|> ... <|assistant|> utterance <|endoftext|>
```
- One **whole dialog** per document; `<|endoftext|>` (8184) stays a *document* separator exactly as in TinyStories — its meaning does not change.
- PersonaChat persona lines render as a `<|system|>` (8187) prefix span (masked from loss).
- Loss mask = assistant utterances only (+ each assistant turn's boundary token so the model learns to *stop*). Train-on-everything is the acceptable fallback if mask plumbing slips a phase — degrades quality, not correctness.
- Encode with `allowed_special="all"` so role markers map atomically (the `encode_corpus.py` discipline); doc-level train/val split on eos (the `load_split` no-leakage discipline). Random windows may still cross dialog boundaries mid-stream — accepted, the standard packed-window regime (dialogs are short relative to corpus; eos separates).
- `<|pad|>` (8188) stays dead — the packed-window regime never pads. Reserved 8189–8191 untouched.

**Vocab-budget effects (verified against `text.py::undecodable_ids_mask`):** live ids grow 547 → ~550 (role tokens go live). The mask formula `set(tok.vocab) | set(tok.special_tokens.values())` already includes all 8 specials, so the dead-id `forbid_ids` mask is **unchanged and still required**. Cold-start note: rows 8185–8187 of the tied `wte`/`lm_head` tensor are effectively at-init when stage 2 begins — expect an early loss spike on role positions; the existing warmup covers it (flag for the stage-2 calibration smoke).

### Pattern 4: Inference-side turn stopping via additive `stop_ids`

**What:** `generate()` gains `stop_ids=None` (defaults to `{eos_id}` — exact v1.0 behavior). Chat inference passes `stop_ids={eos_id, user_id}` so generation halts (stop-without-yield, the D-05 idiom) the moment the model begins a hallucinated user turn.

**Why additive here:** the alternative — terminating every assistant turn with `<|endoftext|>` in training so the v1.0 single-EOS stop suffices — conflates "end of turn" with "end of document", destroys multi-turn context within a dialog, and breaks the TinyStories meaning of eos that EWC is busy protecting. A one-set-membership-check extension to a non-LOCKED function is the cheaper, honest fix. The chat prompt builder in the demo renders history as role-token turns ending with `<|assistant|>` — and **for the recall proof, the Teach tab's facts are never in that prompt**.

### Pattern 5: Dual-task validation telemetry for forgetting curves

**What:** `train()` gains `extra_val_bins: dict[str, path] | None`. Each eval interval also runs `estimate_loss` per extra bin and logs `val_<name>` columns. Stage-2 runs log `val_loss` (dialog, primary — drives `best.pt` selection) + `val_tinystories` (old task). The forgetting curve **is** the `val_tinystories` column plotted over steps, one line per A/B arm.

**Why safe:** `estimate_loss` already snapshots/restores global RNG around its draws — extra calls cannot perturb the training trajectory, so the kill+resume bit-identity contract survives untouched. **CSV discipline:** `CSV_FIELDNAMES` becomes per-run (derived from the extras). `csv.DictWriter` raises on unknown keys, and `CSVLogger` writes the header once per file — so stage-2 runs write **new CSV files** (`logs/finetune_<arm>.csv`); never append new columns to v1.0 `run.csv`. Optionally also log `ewc_penalty` as its own column (diagnosability of λ). Endpoint headline numbers use the deterministic `evaluation/perplexity()` sweep on both tasks' val bins (before/after, per arm).

## Data Flow

### Stage 2 — conversational fine-tune (EWC)

```
DailyDialog zip + personachat_self_original.json        (run-once manual download, like TinyStories)
        ↓ scripts/prepare_dialog_corpus.py
dialog_{train,val}.bin (uint16) + dialog_{train,val}_mask.bin (uint8)     [frozen tokenizer]
        ↓ scripts/finetune_dialog.py
best.pt → vanilla GPT → estimate_fisher(TinyStories train.bin) → EWCPenalty(F, θ*=best, λ)
        ↓ train(model, train_bin=dialog, penalty_fn=ewc, extra_val_bins={"tinystories": val.bin},
                batch_fn → get_batch_memmap_masked, new CSV)
checkpoints/convbase_{latest,best}.pt  (+ fisher/theta_star/ewc_lambda in **extra)
        ↓ run twice via scripts/run_ab_forgetting.py (λ=0 vs λ>0, same seed/budget)
logs/finetune_naive.csv + logs/finetune_ewc.csv → forgetting curves
perplexity() on both val bins per arm → headline A/B table
```

### Stage 3 — teach-then-recall (LoRA)

```
convbase best ckpt → vanilla GPT → load weights → inject_lora(r=8, α=16) → freeze base
        ↓ Teach tab: user facts → templated QA + paraphrase repetition (~dozens of variants)
          → encode (frozen tokenizer, role format, in-memory masked batches) → short train() run
          (~100–300 steps, weight_decay=0, on MPS/CPU — minutes)
        ↓ Chat tab: generate_text_cumulative(forbid_ids, stop_ids={eos, <|user|>}), EMPTY history
recall in a fresh session ⇒ answer comes from weights              [the novel-claim proof]
        ↓ Reset: drop adapter (instant forget)   |   Ship: merge_lora → export_slim (LOCKED schema)
checkpoints/model_personalized_slim.pt  (+ optional adapter.pt, ~1.3 MB)
```

### Visualization flow

```
logs/finetune_*.csv ──→ make_m2_figures.py ──→ results/forgetting_curve.png      (committed)
ckpt pairs (best.pt vs convbase; convbase vs personalized; LoRA ΔW = scale·B@A exact)
                    ──→ per-(layer × 6-projection) mean|ΔW| heatmap + embedding-row strip
                    ──→ results/weight_delta_heatmap_*.png                        (committed)
```

## Suggested Build Order

Dependencies, not phase numbers (the roadmapper owns those):

1. **LoRA core** (`lora/` + tests) — zero data/training deps; pure unit-testable math. Gates: B=0 logits-identity vs vanilla GPT, grad flows only through A/B, merge-equivalence, inject-after-load key discipline, slim round-trip of merged weights.
2. **EWC core** (`continual/` + `loop.py` `penalty_fn` hook + checkpoint extras + tests) — independent of (1); needs only existing TinyStories bins + `best.pt`. Gates: quadratic-form oracle, zero-at-θ*, penalty-once-per-step under grad accum, `penalty_fn=None` ≡ v1.0 trajectory.
3. **Dialog data path** (`prepare_dialog_corpus.py` + masked batch fn + `stop_ids` + tests) — independent of (1) and (2). Gates: atomic role-token encode round-trip, mask alignment, no-leakage split, stop-without-yield.
   *(1), (2), (3) are mutually independent — parallelizable or in any order.*
4. **Stage-2 conversational fine-tune** — needs (2)+(3). Calibration smoke (LR, λ sweep, role-token cold-start check) then the real run → conversational base. This is the long-training phase; **flag for deeper phase research** (λ selection is empirical and the single biggest unknown).
5. **A/B no-forgetting experiment + forgetting curves** — needs (4)'s harness; runs the λ=0 arm + figures. (`run_ablations.py` is the proven calibrated-short-budget template.)
6. **Teach-then-recall demo** — needs (1)+(4). Facts→mini-corpus generation, Blocks UI, clean-room recall protocol, merge/export ship path.
   *(5) and (6) are independent of each other after (4).*
7. **Weight-delta heatmaps + final figures + writeup** — needs checkpoints/CSVs from (4)–(6); pure read-side.

## Anti-Patterns

### 1. Injecting LoRA before loading base weights
**What people do:** wrap the projections at model construction, then `load_state_dict(best.pt)`. **Why wrong:** every wrapped key changes (`q_proj.weight` → `q_proj.base.weight`) — silent `strict=False` partial loads or hard failures. **Instead:** load vanilla → inject → freeze. Pin with a test that loads real weights and asserts logits-identity post-injection.

### 2. Letting EWC state ride outside the checkpoint
**What people do:** keep Fisher/θ* in separate ad-hoc files the resume path silently requires. **Why wrong:** breaks the v1.0 self-contained-checkpoint guarantee — a kill+resume missing the sidecar diverges or crashes mid-run. **Instead:** `**extra` keys in the resume checkpoint (the designed seam); a separate Fisher *cache* is fine as an optimization but resume must not depend on it.

### 3. Appending new columns to an existing CSV
**What people do:** reuse `logs/run.csv` (or its fieldnames constant) for fine-tune runs with extra columns. **Why wrong:** `CSVLogger` writes the header once per file and `DictWriter` raises `ValueError` on unknown keys — and a resumed run would interleave row shapes. **Instead:** new CSV file per run/arm with fieldnames fixed at run start.

### 4. Mis-scaling the EWC penalty under grad accumulation (or cross-device penalty tensors)
**What people do:** add the penalty after the `/accum` divide, or compute it from CPU-resident Fisher/θ* against an MPS model. **Why wrong:** λ silently scales with `grad_accum_steps`; device mismatch crashes mid-run. **Instead:** penalty joins `base_loss` *before* the `/accum` (Pattern-2 snippet); Fisher/θ* moved to `runtime.device` once at penalty construction.

### 5. Terminating assistant turns with `<|endoftext|>`
**What people do:** reuse eos as end-of-turn so the v1.0 stop logic needs no change. **Why wrong:** redefines the exact token whose task-1 statistics EWC is protecting; kills multi-turn context within dialogs. **Instead:** eos stays a document separator; turn-stop = `stop_ids` at inference.

### 6. Expecting 1–2 fact sentences to bake into weights
**What people do:** fine-tune on the literal taught sentence once, then test recall with a differently-phrased question. **Why wrong:** at 13.9M params, single-exposure gradient descent doesn't generalize a fact across phrasings — the demo "fails" for training-recipe reasons, not thesis reasons. **Instead:** the Teach pipeline templates each fact into dozens of QA paraphrases and deliberately overfits (~100–300 steps); document this honestly as the small-model recipe.

### 7. Skipping `forbid_ids` in the new demo
**What people do:** wire the personalization demo's generate call without the dead-id mask. **Why wrong:** re-imports the pre-CR-01 crash class (~29%/400 tokens at extreme settings). **Instead:** the `build_demo`-time `undecodable_ids_mask` pattern from `demo_app.py`, verbatim.

## Integration Points (LOCKED-contract compliance summary)

| LOCKED contract | v2.0 touch | Compliance |
|---|---|---|
| `forward(idx, targets=None) -> (logits, loss)` | Loss masking, LoRA, EWC | Untouched. Masking via `ignore_index=-100` in targets; LoRA wraps submodules, never `forward`; EWC lives in the loop. |
| RNG-state-restore resume | `penalty_fn`, `extra_val_bins`, Fisher pass | `EWCPenalty` is RNG-free; `estimate_loss` self-snapshots; Fisher runs pre-loop under forked RNG. Resume rebuilds the `lora_config` module tree before `load_checkpoint`. |
| `weights_only=True` slim artifacts | Personalized ship path | Always `merge_lora` first → verbatim v1.0 keys → existing `export_slim`/`load_slim`/demo unchanged. Optional `adapter.pt` is tensors+primitives (also safe-loadable). |
| Frozen tokenizer (8192 / eos 8184 / 547 live) | Dialog formatting | No retrain; role specials 8185–8187 already reserved + already decodable in the mask formula; `forbid_ids` unchanged. |
| Open-dict checkpoint | fisher/theta_star/lora_config | Via existing `**extra` — zero format change (the seam exactly as designed). |

## Sources

- `/Users/juliorcoelho/PersonaCore/src/personacore/model/gpt.py`, `training/{loop,loss,data}.py`, `checkpoint.py`, `generation/{core,text}.py`, `tokenizer/special.py`, `logging.py`, `evaluation/perplexity.py`, `scripts/{encode_corpus,demo_app,pretrain_tinystories}.py`, `tests/test_gpt_lora_seam.py` — line-level verification of every seam claimed above (HIGH)
- Hu et al., *LoRA: Low-Rank Adaptation of Large Language Models* (2021) — A/B parameterization, B-zero init, α/r scaling, merge identity (HIGH — paper-canonical; conventions corroborated by microsoft/LoRA loralib)
- Kirkpatrick et al., *Overcoming catastrophic forgetting in neural networks* (PNAS 2017) — EWC quadratic penalty, diagonal Fisher via squared log-likelihood gradients (HIGH)
- PyTorch `F.cross_entropy` default `ignore_index=-100`; AdamW/`clip_grad_norm_` skip `grad=None` params — stable, long-standing API behavior (HIGH)
- [DailyDialog official distribution (zip incl. dialogues_text.txt), CC BY-NC-SA 4.0](http://yanran.li/dailydialog.html) — raw run-once download exists (MEDIUM — verified via search; re-check link health in the data-prep phase)
- [PersonaChat self_original single-JSON raw download (S3, via thomwolf gist)](https://gist.github.com/thomwolf/ecc52ea728d29c9724320b38619bd6a6) and [ParlAI ConvAI2 task](https://github.com/facebookresearch/ParlAI/blob/main/parlai/tasks/convai2/README.md) — zero-budget raw acquisition paths (MEDIUM — verify URL liveness in the data-prep phase)

---
*Architecture research for: PersonaCore v2.0 Weight-Based Memory (LoRA + EWC + conversational fine-tuning + demos)*
*Researched: 2026-06-11*
