# Phase 3: Bigram Baseline & Training Harness - Context

**Gathered:** 2026-06-04
**Status:** Ready for planning

<domain>
## Phase Boundary

A thin, end-to-end **training harness** — tokenize → train → eval → sample → see output —
validated on a **trivial bigram language model** so every load-bearing seam (training loop,
checkpoint/resume, AMP toggle, eval/validation, CSV logging, and the M2 EWC `assemble_loss`
hook) is proven correct **before** the real transformer math (Phase 4) is risked.

**The bigram is disposable; the harness is the deliverable.** The bigram exists only to
exercise the model→loss→logits contract that Phase-4's GPT will implement identically.

**Mode:** MVP (vertical slices) — `**Mode:** mvp` in ROADMAP. Organize work as thin
end-to-end slices (model→loss contract → train loop → eval/checkpoint/resume → sample)
rather than horizontal layers.

**In scope:** the bigram model (MODEL-01); the training loop (AdamW + warmup/cosine LR +
grad clip + grad accum, TRAIN-01); fp32-default with an optional fp16-AMP+GradScaler path
(TRAIN-02); doc-level train/val split + periodic validation loss (TRAIN-03); CSV+matplotlib
logging reproducible across a restart (TRAIN-04); the overfit-a-single-batch correctness gate
(TRAIN-05); the `assemble_loss(..., extra_penalties=())` seam + open-dict checkpoints
(TRAIN-06); a minimal sampling routine to "see output"; and their CPU-only tests.

**Out of scope (other phases):** the GPT decoder + attention/MLP/blocks and exact param sizing
(Phase 4, MODEL-02..07); full-corpus encoding into a `uint16` memmap + the pretraining run
(Phase 5, PRE-01..03); the full-featured `generate()` with top-k/top-p/EOS-aware stopping and
its tests (Phase 6, GEN-01..03) — Phase 3 ships only the minimal sampling needed to prove the
harness produces output; Gradio demo / slim inference checkpoint (Phase 8). LoRA/EWC Fisher
computation is **Milestone 2** — Phase 3 wires the *empty* seam only (plumbing, no penalty math).

</domain>

<decisions>
## Implementation Decisions

### Bigram ↔ Harness Contract (discussed)
- **D-01:** **Lookup-table bigram, GPT-shaped.** Karpathy-canonical `BigramLanguageModel`:
  `nn.Embedding(vocab_size, vocab_size)` where `logits = table(idx)` with shape `(B, T, V)`.
  Trivial, tiny compute, CPU-fine. The ~67M lookup-table params are irrelevant (it's a
  throwaway de-risk model, never pretrained) — what matters is that it exercises the harness.
- **D-02:** **`forward(idx, targets=None) -> (logits, loss)` is the LOCKED model↔harness
  contract** — the *same* signature Phase-4's GPT will implement, so the bigram de-risks the
  exact interface. `forward` computes the **base cross-entropy internally** (nanoGPT-canonical):
  returns `(logits, base_loss)` when `targets` is given, `(logits, None)` otherwise. Phase 4
  replicates this signature unchanged.
- **D-02a:** Reshape discipline for CE: `logits.view(B*T, V)` vs `targets.view(B*T)` — the
  standard nanoGPT flatten — so the same loss call works for the bigram now and the GPT later.

### `assemble_loss` Seam — the M2 EWC hook (discussed, TRAIN-06)
- **D-03:** **Loss is assembled in the TRAINING LOOP, not the model.** The training step calls
  `total = assemble_loss(base_loss, extra_penalties=())`. The model stays pure (only base CE);
  M2's EWC injects the Fisher penalty at the loop level with **zero model changes**. This is the
  whole point of the seam — keep the loop, not the model, as the extension point.
- **D-04:** **`assemble_loss(base_loss, extra_penalties=()) -> base_loss + sum(extra_penalties)`.**
  Each item in `extra_penalties` is a **precomputed scalar tensor**. M1 passes `()` → returns
  `base_loss` **unchanged (identity)**. M2 computes the Fisher-penalty scalar tensor in the loop
  and passes `(penalty,)`. No callbacks, no lazy callables — dead-simple and **fully
  unit-testable now** (identity on empty, additive on non-empty).
- **D-04a:** Unit-test the seam in M1 even though no penalty exists: assert empty-tuple identity
  (`assemble_loss(x, ()) is/equals x`) and additive behavior with a dummy penalty tensor, so the
  M2 EWC contract is locked by a test before EWC is written.

### Open-Dict Checkpoints (TRAIN-06 — already built, reuse as-is)
- **D-05:** Reuse the existing `src/personacore/checkpoint.py` `save_checkpoint`/`load_checkpoint`
  **unchanged** — it is already an open dict with full RNG restore and an `**extra` seam. Phase 3
  must drive it end-to-end (save mid-run → kill → resume same trajectory). **Constraint inherited
  from `checkpoint.py`:** `save_checkpoint` calls `scheduler.state_dict()`, so the LR schedule
  **must be a `torch.optim.lr_scheduler` object** (see D-08), not a bare function.

### Claude's Discretion (user delegated — defaults below are research-grounded)
The user discussed only the two seams above and explicitly delegated the rest. Defaults the
planner/researcher may refine in *mechanics* but should honor in *intent*:

- **D-06 — Harness data path (lean):** Train on a **small committed text fixture** (a handful of
  TinyStories-style docs separated by `<|endoftext|>`) encoded on-the-fly via the **frozen
  Phase-2 tokenizer** (`eos_id=8184`). Produce an in-memory / tiny on-disk `uint16` token array
  and sample **random contiguous windows** (nanoGPT `get_batch` pattern). **Do NOT build the
  full-corpus `uint16` memmap or fetch the full TinyStories corpus** — that is Phase 5 (PRE-01).
  The fixture must contain ≥2 documents so the **doc-level train/val split** (split on doc
  boundaries, never mid-document) demonstrably has **no train/val leakage** (TRAIN-03).
- **D-07 — AMP-on-CPU-CI verification (lean):** The fp16-AMP+GradScaler path is GPU-only, but CI
  is CPU-only. Keep TRAIN-02's `scale → backward → unscale_ → clip → step → update` discipline
  honest via **(a)** a CPU-runnable unit test asserting the *ordering* of the step (e.g. that
  grad-clip happens after `scaler.unscale_(optimizer)`), and **(b)** a **GPU-conditional**
  smoke test (`@pytest.mark.skipif(not cuda)`) that actually runs the AMP path. fp32 is the
  default everywhere; AMP is exercised for correctness, not speed.
- **D-08 — LR schedule mechanics:** Hand-rolled **warmup + cosine** implemented as a
  `torch.optim.lr_scheduler.LambdaLR` (resumable via `state_dict()`, satisfying the
  `checkpoint.py` contract in D-05). Optimizer is `torch.optim.AdamW` with `weight_decay` and
  `grad_clip` from the existing `TrainConfig`.
- **D-09 — Module layout (per Phase-1 D-11, dirs added by their own phase):**
  `src/personacore/model/bigram.py` (the bigram + the shared `forward` contract),
  `src/personacore/training/` (`loop.py` train step, `loss.py` for `assemble_loss`, `data.py`
  for the split + window sampling, `schedule.py` for the LR lambda), and a thin
  `scripts/train_bigram.py` entry point (**no CLI/argparse** — Phase-1 D-04; defaults/kwargs
  only). Phase 4 adds `model/gpt.py` beside the bigram, reusing `training/` untouched.
- **D-10 — Overfit gate (TRAIN-05):** Drive loss toward ~0 on one fixed batch over a bounded
  step budget; assert final loss below a small threshold. CPU-only, fast, deterministic via the
  Phase-1 `seeding` utilities.
- **D-11 — Minimal sampling:** Phase 3 ships only enough sampling (greedy/temperature next-token
  loop) to prove the harness produces text output. The full `generate()` (top-k/top-p,
  EOS-aware stop, tests) is Phase 6 (GEN-01..03) — do not build it here.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase requirements & goal
- `.planning/REQUIREMENTS.md` — MODEL-01, TRAIN-01..TRAIN-06 (the acceptance text this phase
  must satisfy), plus the M2-seam notes on TRAIN-06 and MODEL-07.
- `.planning/ROADMAP.md` §"Phase 3: Bigram Baseline & Training Harness" — goal + 5 success
  criteria + `**Mode:** mvp` + `Depends on: Phase 2`.

### Locked stack & training discipline (P100 constraints)
- `.planning/research/STACK.md` (and `CLAUDE.md` Technology Stack section) — fp16 AMP +
  `GradScaler` only (NO bf16 on Pascal); unscale-before-clip discipline; hand-rolled
  AdamW + cosine-with-warmup; CSV+matplotlib offline logging (no wandb); `torch.compile` skipped
  on P100; `F.scaled_dot_product_attention` allowed (Phase 4, not here).

### Reusable Phase-1/2 code (read before writing the loop)
- `src/personacore/config.py` — `RuntimeConfig` (device/AMP/`autocast()`, bf16-on-Pascal guard),
  `ModelConfig` (`vocab_size=8192`, `eos_id=8184`, `block_size=256`), `TrainConfig`
  (`lr`, `batch_size`, `max_steps`, `warmup_steps`, `grad_clip`, `grad_accum_steps`,
  `weight_decay`, `seed`). The harness reads ALL hyperparameters from these — no new config layer.
- `src/personacore/checkpoint.py` — `save_checkpoint`/`load_checkpoint`: open-dict, full RNG
  restore (resume = same trajectory), `**extra` seam, requires `scheduler.state_dict()`
  (drives D-05/D-08).
- `src/personacore/logging.py` — `CSVLogger`: append-only, restart-safe header logic (drives
  TRAIN-04; the loss curve must reproduce across a kill+resume).
- `src/personacore/seeding.py` — determinism/seed utilities (overfit + reproducibility tests).
- `src/personacore/tokenizer/` — frozen 8192-vocab tokenizer (`encode`/`decode`/`eos_id`) used
  to encode the D-06 fixture; do NOT retrain it.

### Carried-forward decisions
- `.planning/phases/01-scaffolding-reproducible-environment/01-CONTEXT.md` — D-03 (config in
  checkpoint), D-04 (no CLI/argparse), D-11 (module dirs added by their own phase).
- `.planning/phases/02-from-scratch-bpe-tokenizer/02-CONTEXT.md` — D-01 (`vocab_size=8192`
  locked), D-02/D-03 (EOS id `8184`, atomic, do-not-merge-across), D-09 (Phase 5 reuses the
  frozen tokenizer — Phase 3's fixture encode is bounded and does not retrain).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `RuntimeConfig.autocast()` — the single source of AMP truth; the loop's fp16 path wraps the
  forward in `runtime.autocast()` and pairs it with `torch.amp.GradScaler`. fp32 default; AMP
  auto-disabled on CPU; bf16 raises on Pascal — the loop must not re-implement any of this.
- `save_checkpoint(..., **extra)` / `load_checkpoint(...)` — already resumable with RNG restore;
  Phase 3 drives it (the "reproduce loss curve across a restart" success criterion).
- `CSVLogger(path, fieldnames)` — append-only, restart-safe; log `step,train_loss,val_loss,lr,
  tokens,wall_clock` each eval interval (fieldnames are the planner's call).
- `ModelConfig.vocab_size=8192` / `eos_id=8184` — the bigram's table is `(8192, 8192)`; the
  EOS id separates documents in the D-06 fixture and the train/val split.

### Established Patterns
- From-scratch ethos: hand-rolled AdamW schedule + loss assembly; PyTorch primitives only.
- CPU-only test suite (Phase-1 CI) — every Phase-3 test must run GPU-free; the AMP path uses a
  `skipif(not cuda)` guard for the GPU-only smoke test (D-07).
- Atomic commits + Makefile `lint`/`test` gate; thin `scripts/` entry points, no CLI layer.
- nanoGPT idioms: `(logits, loss)` forward, `get_batch` random-window sampling, overfit-one-batch
  sanity gate.

### Integration Points
- `forward(idx, targets) -> (logits, loss)` contract (D-02) → Phase 4's GPT implements it
  unchanged; `training/` is reused untouched.
- `assemble_loss(base, extra_penalties=())` (D-03/D-04) → M2 EWC passes a Fisher-penalty tensor.
- Open-dict checkpoint `**extra` → M2 stores `fisher`/`theta_star` with no format change.
- Frozen tokenizer → Phase 5 (PRE-01) reuses it for the full-corpus memmap (not Phase 3's job).

</code_context>

<specifics>
## Specific Ideas

- **Karpathy nanoGPT / makemore** as the conceptual reference for the bigram, the `get_batch`
  window sampler, the `(logits, loss)` forward, and the overfit-one-batch gate — implemented by
  hand, not vendored.
- The bigram is explicitly a **throwaway de-risk model** — its only job is to make the harness
  fail loudly now (cheap) instead of during the Phase-4 transformer bring-up (expensive).
- `assemble_loss` must be **empty-but-real** in M1: an identity on `()` that is still
  unit-tested, so the EWC seam is contract-locked before EWC exists.

</specifics>

<deferred>
## Deferred Ideas

- **GPT decoder, attention/MLP/blocks, weight tying, param sizing** — Phase 4 (MODEL-02..07).
- **Full-corpus `uint16` memmap + TinyStories fetch + the real pretraining run** — Phase 5
  (PRE-01..03). Phase 3's data path is a bounded committed fixture only (D-06).
- **Full `generate()` (top-k/top-p, EOS-aware stop) + its tests** — Phase 6 (GEN-01..03).
  Phase 3 ships only minimal greedy/temperature sampling to prove output (D-11).
- **EWC Fisher-penalty computation, LoRA adapters** — Milestone 2. Phase 3 wires the empty
  `assemble_loss` seam and the open-dict checkpoint `**extra` slot only.
- **Architecture/LR ablation table** — Phase 7 (EVAL-03).

None of these expanded Phase 3 scope — discussion stayed within the harness boundary.

</deferred>

---

*Phase: 03-bigram-baseline-training-harness*
*Context gathered: 2026-06-04*
