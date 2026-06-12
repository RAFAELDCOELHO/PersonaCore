# Phase 10: EWC Core - Research

**Researched:** 2026-06-12
**Domain:** From-scratch EWC (per-example empirical diagonal Fisher + quadratic penalty) on the v1.0 13.9M GPT, PyTorch 2.7.1, MPS/CPU
**Confidence:** HIGH — all integration seams verified line-by-line against shipped code in this session; mechanics are paper-canonical and were deep-dived in the v2.0 milestone research (`.planning/research/PITFALLS.md` Pitfall 6–8, primary source van de Ven arXiv:2502.11756)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Fisher normalization scheme
- **D-01:** The stored Fisher is **mean-normalized**: after averaging `gᵢ²` over the N
  examples, divide all Fisher tensors by the global mean over trainable coordinates so
  `mean(F) = 1`. λ then reads as "penalty stiffness relative to an average parameter" and
  Phase 12's log-scale sweep grid is interpretable across runs. The scalar divisor is recorded
  in `fisher_meta` so the raw estimate is recoverable.
- **D-02:** The normalization statistic is computed over **all trainable coordinates** (after
  `data_ptr` dedup of the tied embedding) — dead embedding rows included. Their drag on the
  mean is a constant factor λ absorbs; this keeps Fisher estimation decoupled from the
  `forbid_ids` list and makes `mean(F)=1` literally true over the whole penalty domain.
  (Note: because `wte`/`lm_head` are tied, dead vocabulary rows receive small suppression
  gradients at every position — their Fisher entries are tiny-but-nonzero, not structural
  zeros.)

#### Per-example discipline & budget
- **D-03:** Per-example gradients via a **strict batch=1 loop**: one block_size window = one
  example; N independent `zero_grad → forward → CE → backward → accumulate grad²` passes at
  batch size 1, with mean-over-tokens CE matching the training loop's reduction (Pitfall 6).
  EWC-01's "per-example, not batched-gradient squaring" **overrides** ARCHITECTURE.md's
  "batch 1–8" shorthand — with batch > 1, squaring the aggregated gradient is the van de Ven
  bug. Vectorized per-sample grads (`torch.func`) rejected: unneeded at 13.9M and shaky on MPS.
- **D-04:** Production Fisher budget **N ≈ 2000 windows** ("a few thousand" per PITFALLS, with
  margin over ARCHITECTURE's 200–500 floor). Minutes of wall-clock at batch=1 on the M3. N is
  recorded in `fisher_meta`.
- **D-05:** Fisher estimation ships a **lightweight empirical convergence check** alongside the
  unit-test oracle: split the N windows into two disjoint halves, compare the half-estimates
  (rank correlation + relative mean change vs the full estimate), report the numbers in the
  smoke output and store them in `fisher_meta`. "N is enough" becomes a measured claim, in the
  project's evidence-over-assertion register.

### Claude's Discretion

The user delegated two surfaced gray areas to Claude/planner judgment, guided by the research
docs (`.planning/research/ARCHITECTURE.md`, `PITFALLS.md`):

- **Real-weights Fisher run & artifact policy** — smoke-scale proof vs producing the production
  `fisher_tinystories.pt` cache Phase 12/13 arms share; whether the cache file meets the
  safe-load/schema-version bar (Phase 9 `load_adapter` precedent) or stays a plain gitignored
  `torch.save`; script packaging (Phase 9's 09-04 real-weights smoke script is the precedent).
  Constraints that bound the choice: resume checkpoints must stay self-contained (θ*/Fisher by
  value via `**extra` — the cache is an optimization only, ARCHITECTURE anti-pattern 2), and
  Phase 10's success criterion 1 requires Fisher actually estimated at `best.pt` over
  TinyStories batches in this phase.
- **loop.py touch scope** — land only `penalty_fn=None` (the phase's minimum) or also
  `extra_val_bins` + per-run derived CSV fieldnames in the same touch (ARCHITECTURE lists both
  as v2.0 additive loop changes; retention telemetry isn't exercised until Phase 12). Either
  way: defaults must reproduce v1.0 bit-for-bit and the penalty joins `base_loss` **before**
  the `/accum` divide (ARCHITECTURE Pattern 2 / anti-pattern 4).

Also Claude's discretion: λ placeholder convention for Phase-10 tests/smoke, exact
file/module naming within `continual/`, fisher_meta field set (beyond source/N/seed/
anchor-provenance/normalizer/convergence stats already implied), and test-suite organization.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EWC-01 | From-scratch empirical diagonal Fisher estimated from per-example gradients over TinyStories batches (not batched-gradient squaring), normalized, stored with anchor θ* via the open-dict checkpoint seam | Pattern 1 (estimate_fisher skeleton with batch=1 `torch.autograd.grad` loop, local RNG, mean-normalization), Pattern 3 (θ*/Fisher dedup + `**extra` persistence — `named_parameters()` dedup behavior VERIFIED in-venv this session), Pitfalls 1–4, Code Examples 1–3, timing VERIFIED (N=2000 ≈ 0.6 min on MPS) |
| EWC-02 | Quadratic penalty `(λ/2)·Σ Fᵢ·(θᵢ−θ*ᵢ)²` plugged in via `assemble_loss(..., extra_penalties=())`; penalty exactly 0 at the anchor (unit test) | Pattern 2 (EWCPenalty callable + exact loop.py:136–139 splice, penalty before `/accum`), Code Example 4, exact-zero-at-anchor argument (bitwise-zero subtraction in fp32), Pitfall 5 (accum scaling), test map in Validation Architecture |

EWC-03 (λ sweep) is **explicitly Phase 12's** — no λ calibration in this phase; λ appears only as a placeholder constant in tests/smoke.
</phase_requirements>

## Summary

Phase 10 builds the milestone's second headline from-scratch deliverable: `continual/` (Fisher
estimation + EWC penalty). Everything it needs already exists and was re-verified in this
session: `assemble_loss(base_loss, extra_penalties=())` is shipped and seam-test-pinned; the
hardcoded `assemble_loss(base_loss, ())` splice point sits at `loop.py:138` inside
`_optimizer_step`; `save_checkpoint(**extra)`'s docstring reserves `fisher`/`theta_star`;
`best.pt` (166.8 MB, val_loss 0.7378) and `train.bin`/`val.bin` exist on disk; the venv runs
Python 3.11.15 + torch 2.7.1 with MPS available; the suite currently collects **190 tests**
(the roadmap's "137" and CONTEXT's "180" both predate later additions — use 190 as the
all-green bar).

Two load-bearing facts were empirically verified in-venv this session. First,
`model.named_parameters()` (default `remove_duplicate=True`) yields the tied `wte`/`lm_head`
tensor **exactly once** (100 entries, 13,891,584 params, key `wte.weight`; `lm_head.weight`
absent) while `state_dict()` carries it under **both** keys sharing storage — so the Fisher/θ*
snapshot must be built from `named_parameters()`, never `state_dict()`, and a test must pin the
single-entry property. Second, one forward+backward at batch=1/block=256 costs ~18.6 ms on MPS
(~43.6 ms CPU), so the production N=2000 Fisher pass is **under a minute on the M3** — D-04's
budget is comfortably affordable, which settles the discretion question in favor of producing
the real production cache in this phase.

The mechanics themselves are paper-canonical and the v2.0 milestone research already did the
correctness deep-dive (van de Ven 2025: squaring batch-aggregated gradients is the most-copied
EWC bug; per-example `grad²` is the fix). This phase's risk is therefore not "what algorithm"
but implementation discipline: tied-tensor dedup, matching the training loss reduction by
reusing the model's own forward, RNG isolation of the Fisher pass (note: `torch.random.fork_rng`
does **not** cover NumPy — window draws need a local `np.random.Generator`), penalty placement
before the `/accum` divide, and bit-preserving the v1.0 trajectory when `penalty_fn=None`.

**Primary recommendation:** Build `continual/fisher.py` (`estimate_fisher` → `(fisher, fisher_meta)`,
batch=1 `torch.autograd.grad` loop over `named_parameters()`, local `np.random.Generator` window
draws, mean-normalization, half-split convergence stats) and `continual/ewc.py` (`EWCPenalty`
callable, device-moved once at construction); splice `penalty_fn=None` into `_optimizer_step`
exactly per ARCHITECTURE Pattern 2; persist via `save_checkpoint(**extra)`; run the production
N=2000 estimation at `best.pt` via a thin smoke script (09-04 shape) that writes a
schema-versioned, `weights_only=True`-safe `checkpoints/fisher_tinystories.pt` cache.

## Architectural Responsibility Map

This is a Python ML library, not a web app — "tiers" are the project's module layers.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Fisher estimation (per-example grad² accumulation, normalization, convergence stats) | `continual/fisher.py` (NEW) | `training/data.py` (window-draw discipline) | Pure function of model + memmap; the headline from-scratch deliverable, self-contained and paper-traceable |
| Quadratic penalty `(λ/2)·Σ F(θ−θ*)²` | `continual/ewc.py` (NEW) | — | A callable `(model) -> scalar tensor`; RNG-free, deterministic in params (resume-equality contract survives) |
| Loss assembly | `training/loss.py` (UNCHANGED) | — | `assemble_loss` is the designed seam; consumed verbatim (D-04 contract: precomputed scalars, no callables in the tuple) |
| Loop integration (`penalty_fn=None` kwarg) | `training/loop.py` (MODIFIED, additive) | — | The ONLY place the penalty is evaluated; one kwarg threaded into `_optimizer_step`, default `None` ≡ v1.0 bit-for-bit |
| θ*/Fisher persistence | `checkpoint.py` `**extra` (UNCHANGED) | cache exporter (see Open Q2) | Docstring line 77 reserves exactly `fisher`/`theta_star`; zero format change |
| Real-weights proof + production cache | `scripts/` (NEW thin script) | — | Phase 9's `train_adapter_smoke.py` (09-04) is the exact precedent: no-CLI, `_REPO_ROOT` constants, explicit `SystemExit` checks, gitignored outputs |
| Correctness verification | `tests/` (NEW: fisher / penalty / loop files) | — | CPU-only, GPU-free house discipline; MPS reductions are not bit-stable, so oracles run on CPU |

**Misassignment guards:** the penalty must NOT live in `model/gpt.py` (purity rule — never
edited); Fisher must NOT be computed inside `train()` (it runs before training or in its own
script); normalization must NOT live in the penalty (it is a property of the stored Fisher,
D-01).

## Standard Stack

### Core

Zero new dependencies. Everything is implemented with the pinned v1.0 environment (verified
in-venv 2026-06-12):

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| torch | 2.7.1 (installed; pin `2.7.*`) | autograd per-example grads, tensor ops, `torch.save`/`load` | `[VERIFIED: in-venv import]` — the project's pinned framework; plain autograd is the from-scratch boundary |
| numpy | 2.x (installed) | memmap window draws, fp64 statistics, hand-rolled Spearman | `[VERIFIED: in-venv]` — existing data path dependency |
| pytest | 8.x (installed) | unit tests | `[VERIFIED: 190 tests collect in 0.61 s]` |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| stdlib `dataclasses` | — | optional `FisherConfig` mirroring Phase 9's `LoRAConfig` house pattern; `asdict` → `fisher_meta` primitives | If the planner wants a config surface; plain kwargs also acceptable |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| batch=1 `torch.autograd.grad` loop | `torch.func.vmap`/`grad` per-sample grads | **Rejected by D-03** — unneeded at 13.9M (measured <1 min for N=2000) and shaky on MPS |
| hand-rolled numpy Spearman | scipy.stats.spearmanr | **scipy is NOT in the stack** — adding it for one statistic violates the zero-new-deps posture; ranks via double-argsort + `np.corrcoef` is ~5 lines |
| `loss.backward()` + read `p.grad` + `zero_grad` | `torch.autograd.grad(loss, params)` | Both are "plain autograd" (D-03 compliant). **Recommend `torch.autograd.grad`**: no model `.grad` state mutation, no zero_grad bookkeeping, returns grads aligned with the deduped param list |

**Installation:** none — `make install` already provides everything.

**Version verification:** performed in-session: Python 3.11.15, torch 2.7.1 (MPS available),
190 tests collected. No registry lookups needed (no new packages).

## Package Legitimacy Audit

No external packages are installed by this phase. **Packages removed due to slopcheck [SLOP]
verdict:** none. **Packages flagged as suspicious [SUS]:** none. (slopcheck not run — nothing
to check.)

## Architecture Patterns

### System Architecture Diagram

```
checkpoints/best.pt ──torch.load(weights_only=False, trusted)──► vanilla GPT (anchor weights)
                                                                       │
                      ┌────────────────────────────────────────────────┤
                      ▼                                                ▼
        θ* snapshot                                      estimate_fisher(model, train.bin, ...)
        {name: p.detach().clone().cpu()                      │  windows ← local np.random.Generator(seed)
         for name, p in model.named_parameters()}            │  (global RNG NEVER touched)
        — deduped by construction (verified:                 │  N=2000 × [batch=1 forward → CE (model's own
          tied tensor appears once, as wte.weight)           │   mean-over-tokens reduction) → autograd.grad
                      │                                      │   → accumulate g² on device, fp32]
                      │                                      │  two half-accumulators → convergence stats
                      │                                      ▼  (Spearman + rel. mean change, fp64 on CPU)
                      │                              mean over N → mean-normalize (D-01, normalizer
                      │                              recorded) → (fisher, fisher_meta)
                      │                                      │
                      └──────────────────┬───────────────────┘
                                         ▼
                    EWCPenalty(fisher, theta_star, lam, device)
                    [fisher/θ* moved to device ONCE at construction; keys validated]
                                         │ penalty_fn (callable: model → scalar tensor)
                                         ▼
        train(..., penalty_fn=ewc) → _optimizer_step, per micro-batch (loop.py:136–139):
            _, base_loss = model(xb, yb)
            penalties = (penalty_fn(model),) if penalty_fn is not None else ()
            total = assemble_loss(base_loss, penalties)     # D-04: precomputed scalar
            loss = total / accum                            # penalty BEFORE the /accum divide
            ... v1.0 scale→backward→unscale→clip→step→update→scheduler ordering UNCHANGED
                                         │
                 ┌───────────────────────┴───────────────────────────┐
                 ▼                                                   ▼
   save_checkpoint(..., fisher=, theta_star=,        checkpoints/fisher_tinystories.pt
     ewc_lambda=, fisher_meta=)  [open-dict **extra,   (CACHE — optimization only; resume
     resume stays self-contained]                       must NEVER depend on it)
```

### Recommended Project Structure (additions only)

```
src/personacore/
└── continual/                 # NEW package — the from-scratch EWC deliverable
    ├── __init__.py            # exports estimate_fisher, EWCPenalty (+ cache loader if it lives here)
    ├── fisher.py              # estimate_fisher → (fisher: dict[str, Tensor], fisher_meta: dict)
    └── ewc.py                 # EWCPenalty: callable (model) -> scalar tensor
src/personacore/training/
└── loop.py                    # MODIFIED (additive): +penalty_fn=None threaded into _optimizer_step
scripts/
└── estimate_fisher_tinystories.py   # NEW: real-weights run at best.pt, N=2000, writes the cache
tests/
├── test_fisher.py             # oracle, anti-batched fixture, non-negativity, dedup, normalization,
│                              # determinism, RNG purity, eval-mode restore
├── test_ewc_penalty.py        # quadratic-form oracle, exact-zero at θ*, λ linearity, gradient check
├── test_loop_penalty_fn.py    # None ≡ default trajectory, zero-penalty ≡ None, once-per-accum-step
└── test_fisher_checkpoint.py  # **extra round-trip; cache schema round-trip (may merge into test_fisher.py)
```

Module naming `fisher.py` + `ewc.py` is **already converged** in the v2.0 research
(SUMMARY/ARCHITECTURE both name it) — do not re-litigate.

### Pattern 1: `estimate_fisher` — strict batch=1 per-example loop (D-03)

**What:** N independent passes at batch size 1; per pass: draw one window, forward through the
model's own `forward(xb, yb)` (this **is** how the loss-reduction match is guaranteed — the CE
and its mean-over-tokens reduction are the LOCKED model tail, the same op the training loop
optimizes), `torch.autograd.grad(loss, params)`, accumulate `g²` in fp32 on device. Average
over N, then mean-normalize per D-01/D-02.

**Key facts (verified this session):**
- `params = [p for _, p in model.named_parameters()]` contains the tied tensor **once**;
  `autograd.grad` returns its total gradient (both tying paths summed) — exactly the correct
  Fisher for the tied parameterization. No manual dedup needed *if* iteration uses
  `named_parameters()`; the `data_ptr` test pins it anyway (belt and braces).
- `model.eval()` before the loop (dropout is 0.0 in this config, but eval is the discipline —
  Pitfall 6); restore the prior `model.training` flag afterwards (do not blindly
  `model.train()` — the model may be used for inference next).
- The forward in eval mode consumes **zero** torch RNG; the only RNG consumer is window
  sampling. Use a **local `np.random.Generator`** (see Pitfall 3 — `fork_rng` doesn't cover
  NumPy). `estimate_fisher` is then fully RNG-pure: global random/numpy/torch streams are
  bit-unchanged after the call (testable).
- Accumulate in fp32 on device. **MPS has no float64** — compute the normalizer and
  convergence statistics in fp64 only after moving sums/flat arrays to CPU.
- No autocast anywhere in the Fisher pass (it's fp32-only by design; on the P100 fallback,
  fp16 squared-gradients underflow — PITFALLS integration gotcha).

**Convergence check (D-05):** maintain two accumulators (windows 0..N/2−1 → `acc_a`,
N/2..N−1 → `acc_b`); full estimate = (acc_a + acc_b) / N. Metrics: Spearman rank correlation
between flattened half-estimates (hand-rolled: ranks via double `argsort`, then
`np.corrcoef`; fp64 on CPU; ~13.9M elements sorts in ~1–2 s) and relative mean change of each
half vs the full estimate. Report in smoke output; store floats in `fisher_meta`. **Report,
don't gate** — D-05 makes "N is enough" a measured claim, not a threshold assertion.

### Pattern 2: `EWCPenalty` as a loop-evaluated `penalty_fn` (the exact splice)

**What:** constructed once per run with `(fisher, theta_star, lam, device)`; moves Fisher/θ*
to `device` once at construction (ARCHITECTURE anti-pattern 4); validates
`fisher.keys() == theta_star.keys()` and that every key names a model parameter — fail loudly
at construction, not mid-run. Called per micro-batch: looks up params by name
(`dict(model.named_parameters())` — ~100 entries, negligible) and returns
`(lam / 2) * Σ_name (F_name * (p_name − θ*_name)²).sum()` as a scalar tensor on the model's
device, differentiable w.r.t. `p`.

**The loop change** — verified against current `loop.py` (splice at lines 136–139 inside
`_optimizer_step`; `train()` gains `penalty_fn=None` and threads it down):

```python
with runtime.autocast():
    _, base_loss = model(xb, yb)
    penalties = (penalty_fn(model),) if penalty_fn is not None else ()
    total = assemble_loss(base_loss, penalties)   # D-04: still precomputed scalars
    loss = total / accum                          # penalty joins BEFORE the /accum divide
```

- Penalty per micro-batch ÷ accum = exactly **one** full penalty contribution per optimizer
  step (test-pinned).
- `summed += float(base_loss.item())` stays base-loss-only — the logged `train_loss` keeps its
  v1.0 meaning. Penalty observability for Phase 10 comes from calling `penalty_fn` directly in
  the smoke; the `ewc_penalty` CSV column is Phase 12's concern.
- Autocast note: on the primary MPS/CPU path autocast is disabled (no dtype effect). On the
  P100 fp16 fallback, the penalty's elementwise ops run in the params' fp32 dtype under
  autocast's type-promotion rules — no underflow risk from the splice position. No need to
  exempt the penalty from the autocast block; keep the ARCHITECTURE snippet verbatim.

**Exact-zero at the anchor:** θ* entries are detached clones of the anchor params. When
`p == θ*` bitwise, `(p − θ*)` is exactly zero in fp32, so the penalty is exactly `0.0` for any
λ and any F — the unit test asserts `penalty.item() == 0.0` (equality, not allclose), on CPU.

### Pattern 3: Persistence — θ*/Fisher via `**extra`, snapshot from `named_parameters()`

**What:** `save_checkpoint(..., fisher=fisher, theta_star=theta_star, ewc_lambda=lam,
fisher_meta=meta)` — the docstring reserves exactly this; `load_checkpoint` returns the full
dict so callers read the extras back. θ* duplicates `best.pt`'s weights **by value**
deliberately: resume checkpoints stay self-contained (no sidecar dependency —
anti-pattern 2).

**The dedup rule (verified):** snapshot θ* and key Fisher from `named_parameters()` (deduped:
tied tensor once, under `wte.weight`). Never snapshot from `state_dict()` — it carries the
shared storage under both `wte.weight` and `lm_head.weight` and the penalty would
double-count that 3.1M-param tensor. The test asserts: exactly one Fisher/θ* entry whose
storage is the tied tensor; `lm_head.weight` absent from both dicts; survives a
save/load round-trip (compare keys + values after reload — `data_ptr`s legitimately change
across serialization).

**Size check:** Fisher + θ* ≈ 2 × 55.6 MB fp32 on top of the ~159 MB full checkpoint —
fine on local disk, gitignored (existing `.gitignore` covers `checkpoints/`).

### Pattern 4: The real-weights smoke script (09-04 precedent) + production cache

**What:** `scripts/estimate_fisher_tinystories.py` mirrors `train_adapter_smoke.py` exactly in
shape: module docstring stating what it proves, `os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")`
before importing torch, `_REPO_ROOT` path constants, named tuned constants (`N_EXAMPLES = 2000`,
`SEED`, λ placeholder), `preflight_device(strict=True)` gate, explicit `raise SystemExit`
checks (never strippable `assert`s), gitignored outputs.

**Recommended proof checks in the script** (each a `SystemExit` on failure):
1. All Fisher entries finite and ≥ 0.
2. Exactly one entry for the tied storage; `lm_head.weight` absent.
3. `mean(F) == 1` within fp32 tolerance post-normalization; raw normalizer > 0 recorded.
4. `EWCPenalty(fisher, θ*, λ)(model) == 0.0` exactly at the anchor.
5. Perturb one param slightly → penalty > 0 (sanity that the penalty sees drift).
6. Convergence stats printed + stored (report, not gate — D-05).

**Cache artifact (discretion resolution — recommended):** produce the **production** cache in
this phase. Rationale: the run costs <1 minute (measured), success criterion 1 already
requires a real estimation at `best.pt`, and Phase 12/13's two A/B arms then share one
estimation pass. Format: `{schema_version, fisher, fisher_meta, anchor_fingerprint}` where
`anchor_fingerprint` is the provenance trio read from `best.pt` (`git_sha`/`step`/`val_loss` —
the `export_adapter` D-02 precedent). All tensors + primitives → meets the
`weights_only=True` safe-load bar; give it a `FISHER_SCHEMA_VERSION` and a single load
choke point with structural validation (the `load_adapter` discipline). Do **not** put θ* in
the cache — it is recoverable from `best.pt`, which the fingerprint pins; the cache is an
optimization only and resume never depends on it.

### Anti-Patterns to Avoid

- **Squaring batch-aggregated gradients** (the van de Ven bug): with batch>1, cross-terms
  don't vanish and the result is not the Fisher. D-03's batch=1 loop is the law; the
  anti-batched unit fixture (Code Example 2) makes the distinction structurally testable.
- **Snapshotting θ*/Fisher via `state_dict()`**: double-counts the tied tensor (verified —
  two keys, one storage). Snapshot via `named_parameters()`.
- **EWC state outside the checkpoint as a resume dependency** (anti-pattern 2): the cache file
  is an optimization; resume checkpoints carry Fisher/θ* by value.
- **Penalty after the `/accum` divide** (anti-pattern 4): λ silently scales with
  `grad_accum_steps`.
- **Cross-device penalty tensors**: CPU-resident Fisher/θ* against an MPS model crashes
  mid-run; move once at construction.
- **Reimplementing the CE/reduction in fisher.py**: reuse `model(xb, yb)` — the reduction
  mismatch (mean-vs-sum, ~256× Fisher magnitude shift) is Pitfall 6's deadliest variant.
- **`torch.random.fork_rng` as the only RNG guard**: it does not fork NumPy, and the window
  draws are NumPy (see Pitfall 3).
- **Computing fp64 statistics on MPS**: MPS has no float64 — move to CPU first.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Loss + reduction for Fisher | A fisher-local CE | the model's own `forward(xb, yb)` | The LOCKED tail (`F.cross_entropy` mean over B·T) is the exact objective the loop optimizes; any reimplementation risks the reduction-mismatch bug |
| Window sampling discipline | New memmap indexing | `get_batch_memmap`'s idiom (re-open memmap per call, `len−block−1` start bound, uint16→int64) | Bounds + RSS-leak discipline already proven; either add an additive `rng=None` kwarg to `get_batch_memmap` or mirror its ~6 lines privately in `fisher.py` with a local Generator |
| Persistence format | A new checkpoint/file format | `save_checkpoint(**extra)` + (for the cache) the `export_adapter`/`load_adapter` schema-version pattern | The seams were designed for exactly this; zero format change |
| Loop orchestration | Any restructure of `_optimizer_step` | One additive `penalty_fn=None` kwarg | Success criterion 4 (bit-identity) forbids anything else |
| Per-sample grad vectorization | `torch.func`/vmap machinery | plain batch=1 `torch.autograd.grad` loop | D-03 locked; measured cost is <1 min for N=2000 |

**Inversion — must hand-roll:** Spearman rank correlation (scipy is not a dependency; double
`argsort` + `np.corrcoef` in fp64 on CPU) and the Fisher/penalty math itself (the from-scratch
boundary: no opacus, no torch.func, no library EWC).

**Key insight:** every "build" decision in this phase is really a "reuse the designed seam"
decision — the only genuinely new math is ~60 lines across `fisher.py` and `ewc.py`, and the
correctness burden lives in the tests, not the implementation size.

## Common Pitfalls

### Pitfall 1: Tied-tensor double counting (PITFALLS P7)
**What goes wrong:** Fisher/θ* built from `state_dict()` carries the shared `wte`/`lm_head`
storage under two keys → the penalty double-counts 3.1M params; λ semantics shift.
**Why it happens:** `state_dict()` does not deduplicate shared storage (verified this session).
**How to avoid:** snapshot from `named_parameters()` (deduplicates by default — verified: 100
entries, `lm_head.weight` absent); pin with a `data_ptr`-based test mirroring
`test_gpt_weight_tying.py` / `test_ablation_config.py::count_parameters`.
**Warning signs:** Fisher dict has 101 keys; penalty at small uniform drift is ~1.23× the
analytic value (the tied tensor's share counted twice).

### Pitfall 2: The batched-gradient Fisher (PITFALLS P6, van de Ven arXiv:2502.11756)
**What goes wrong:** squaring a gradient aggregated over >1 example is not the Fisher;
required λ shifts orders of magnitude; the Phase 13 A/B becomes untrustworthy.
**Why it happens:** PyTorch makes batch gradients easy; per-example awkward.
**How to avoid:** strict batch=1 loop (D-03). Unit-test with a fixture where per-example and
batched estimates **provably differ**: two examples with opposing gradients give per-example
Fisher = g² but batched-gradient "Fisher" = 0 (Code Example 2).
**Warning signs:** Fisher estimate changes dramatically with batch size; penalty(θ*) ≠ 0.

### Pitfall 3: `fork_rng` does not cover NumPy — Fisher pass perturbs the training stream
**What goes wrong:** `get_batch_memmap` draws via **global** `np.random`; running the Fisher
pass in-process before `train()` advances the global NumPy stream, so a with-Fisher run and a
no-Fisher run (e.g., Phase 12's λ=0 arm) diverge in data order despite identical seeds.
`torch.random.fork_rng` only forks torch generators — it does not protect this.
**How to avoid:** `estimate_fisher` takes an explicit `seed` and uses its own
`np.random.Generator` (`np.random.default_rng(seed)`) for all window draws; it never touches
global RNG (forward in eval mode consumes no torch RNG either). Test: capture
`(random.getstate(), np.random.get_state(), torch.get_rng_state())` before/after
`estimate_fisher` and assert bit-equality (the loop's `_rng_state` idiom).
**Warning signs:** the smoke run before training changes step-1 training loss vs a run that
loads the cache instead.

### Pitfall 4: MPS numerics — no fp64, non-bit-stable reductions
**What goes wrong:** computing the normalizer/Spearman in float64 on MPS raises; comparing
exact values across MPS runs flakes (reduction order is not bit-stable).
**How to avoid:** accumulate `g²` in fp32 on device; move to CPU and upcast to fp64 only for
statistics. All correctness oracles run on CPU (house discipline — tests are CPU-only/GPU-free
already); the smoke script's checks use tolerances except the exact-zero-at-anchor check
(bitwise-zero subtraction is device-independent).
**Warning signs:** `TypeError: Cannot convert a MPS Tensor to float64`; flaky equality
assertions only on MPS.

### Pitfall 5: Penalty × grad-accum mis-scaling (ARCHITECTURE anti-pattern 4)
**What goes wrong:** penalty added after `loss = total / accum` (or added once per optimizer
step but then divided) makes effective λ depend on `grad_accum_steps`.
**How to avoid:** the Pattern-2 splice adds the penalty per micro-batch **before** `/accum` —
N micro-batches × (penalty/N) = exactly one penalty per step. Test: with a penalty whose
gradient is analytically known (e.g., pure `EWCPenalty` at a displaced θ), assert the
post-step parameter delta matches between `accum=1` and `accum=4` runs on identical effective
batches (the existing `test_grad_accum_equivalent_to_big_batch` synthetic-data idiom makes
this directly reusable).
**Warning signs:** Phase 12 λ* changes when `grad_accum_steps` changes.

### Pitfall 6: "Bit-identical to v1.0" asserted, not measured
**What goes wrong:** after editing `loop.py`, there is no v1.0 binary to diff against —
"defaults reproduce v1.0" becomes a code-review claim.
**How to avoid:** capture a **golden trajectory fixture before the loop edit** (first task of
the plan: run a short seeded fixture train — e.g., 5 steps on `tests/fixtures/bigram_corpus.txt`
with `seed_everything(1234)` — and record per-step losses + a param checksum to a committed
JSON). The post-edit test replays the run with defaults and asserts exact equality. Plus: the
full 190-test suite green (it embeds trajectory-equality, resume, and overfit-gate pins), and
a `penalty_fn=None` vs kwarg-omitted equality test.
**Warning signs:** the plan's verification step says "code inspection shows the path is
unchanged" with no executed evidence.

### Pitfall 7: Degenerate normalizer / silent NaN
**What goes wrong:** a zero or non-finite global mean (all-zero grads, a NaN window) makes the
normalized Fisher inf/NaN and everything downstream garbage — on MPS, silently.
**How to avoid:** guard in `estimate_fisher`: assert every accumulated tensor is finite and
the raw mean is > 0 before dividing; the smoke's `SystemExit` finiteness check repeats this on
real weights (PITFALLS P5 fail-fast posture).
**Warning signs:** penalty is NaN at the first training step; normalizer recorded as 0.0.

## Code Examples

Verified patterns — seam line numbers checked against shipped code this session.

### 1. estimate_fisher skeleton (batch=1, RNG-pure, dedup-by-construction)

```python
# Source: D-03/D-01/D-05 + verified named_parameters dedup + training/data.py idiom
def estimate_fisher(model, bin_path, *, n_examples, block_size, device, seed, normalize=True):
    was_training = model.training
    model.eval()                                   # Pitfall 6 discipline (dropout=0.0 anyway)
    named = list(model.named_parameters())         # tied tensor appears ONCE (verified)
    params = [p for _, p in named]
    rng = np.random.default_rng(seed)              # LOCAL generator — global RNG untouched
    acc_a = [torch.zeros_like(p, device=device) for p in params]   # two half-accumulators (D-05)
    acc_b = [torch.zeros_like(p, device=device) for p in params]
    data_len = len(np.memmap(bin_path, dtype=np.uint16, mode="r"))
    for i in range(n_examples):
        data = np.memmap(bin_path, dtype=np.uint16, mode="r")      # re-open per draw (RSS discipline)
        start = int(rng.integers(0, data_len - block_size - 1))
        x = torch.from_numpy(data[start:start + block_size].astype(np.int64))[None].to(device)
        y = torch.from_numpy(data[start + 1:start + 1 + block_size].astype(np.int64))[None].to(device)
        _, loss = model(x, y)                      # the model's OWN CE: mean-over-tokens, matched
        grads = torch.autograd.grad(loss, params)  # no .grad mutation, no zero_grad bookkeeping
        acc = acc_a if i < n_examples // 2 else acc_b
        for a, g in zip(acc, grads):
            a.add_(g.detach() ** 2)
    # full = (acc_a + acc_b) / N; convergence stats from halves (fp64 on CPU — MPS has no fp64)
    # normalize: divide every tensor by the global mean over all coordinates (D-01/D-02)
    # build fisher = {name: tensor.cpu()}, fisher_meta = {...}; restore model mode
    if was_training:
        model.train()
    return fisher, fisher_meta
```

### 2. The anti-batched-Fisher discriminating fixture (the P6 oracle)

```python
# Source: van de Ven arXiv:2502.11756 (the cross-terms argument), made structural:
# two examples with OPPOSING gradients -> per-example Fisher = g^2, batched "Fisher" = 0.
# Tiny 1-layer model; expected per-example Fisher computed by an explicit autograd loop
# in the test itself (brute-force oracle), compared to estimate_fisher's output.
# A second assert computes the batched-gradient estimate and proves it DIFFERS,
# pinning that the implementation cannot regress to the bug.
```

### 3. θ* snapshot + checkpoint round-trip (the dedup + persistence test core)

```python
# Source: verified named_parameters/state_dict behavior + checkpoint.py docstring seam
theta_star = {n: p.detach().clone().cpu() for n, p in model.named_parameters()}
assert "lm_head.weight" not in theta_star and "wte.weight" in theta_star   # dedup pinned
save_checkpoint(path, model=model, optimizer=opt, scheduler=sched, step=0,
                model_config=mcfg, train_config=tcfg, git_sha=git_sha(),
                fisher=fisher, theta_star=theta_star, ewc_lambda=1.0, fisher_meta=meta)
ckpt = load_checkpoint(path, model=model2)
assert ckpt["fisher"].keys() == fisher.keys()      # reload intact (values via torch.equal)
```

### 4. EWCPenalty (the EWC-02 deliverable)

```python
# Source: Kirkpatrick et al. 2017 (PNAS) quadratic form; ARCHITECTURE Pattern 2 component spec
class EWCPenalty:
    def __init__(self, fisher, theta_star, lam, device):
        assert fisher.keys() == theta_star.keys()              # fail loudly at construction
        self.fisher = {n: f.to(device) for n, f in fisher.items()}        # move ONCE
        self.theta_star = {n: t.to(device) for n, t in theta_star.items()}
        self.lam = lam

    def __call__(self, model):
        params = dict(model.named_parameters())                # ~100 entries, negligible
        total = None
        for name, f in self.fisher.items():
            d = params[name] - self.theta_star[name]           # exact 0.0 at the anchor
            term = (f * d * d).sum()
            total = term if total is None else total + term
        return (self.lam / 2.0) * total                        # scalar tensor, grads flow to params
```

### 5. The loop splice (verified against loop.py:136–139)

```python
# Source: ARCHITECTURE Pattern 2, current code verified — _optimizer_step gains penalty_fn,
# train() gains penalty_fn=None and threads it through. The ONLY semantic change:
with runtime.autocast():
    _, base_loss = model(xb, yb)
    penalties = (penalty_fn(model),) if penalty_fn is not None else ()
    total = assemble_loss(base_loss, penalties)
    loss = total / accum
```

### 6. Hand-rolled Spearman (no scipy)

```python
# Source: definition — Spearman = Pearson correlation of ranks; fp64 on CPU
def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    ra = np.empty_like(a, dtype=np.float64); ra[np.argsort(a)] = np.arange(len(a))
    rb = np.empty_like(b, dtype=np.float64); rb[np.argsort(b)] = np.arange(len(b))
    return float(np.corrcoef(ra, rb)[0, 1])
# Ordinal ranks (no tie-averaging) — adequate for a convergence report over 13.9M floats;
# document the method string in fisher_meta.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Squaring mini-batch gradients ("the most-copied EWC bug") | Per-example `grad²` accumulation | van de Ven, ICLR 2025 blogpost track (arXiv:2502.11756) | This phase's D-03 is the current standard; λ values from buggy implementations are non-portable |
| Exact Fisher (expectation over all classes) | Empirical Fisher over ground-truth next tokens, variant **named in the writeup** | accepted practical standard for LMs | Cheap, defensible; `fisher_meta["variant"]` records it |
| Online/multi-task EWC chains, KFAC | Single-anchor diagonal EWC | project Out-of-Scope table | No γ-decay machinery; diagonal is the accepted reproduction standard |

**Deprecated/outdated for this project:** `torch.func` per-sample grads (rejected by D-03);
opacus/library EWC (from-scratch boundary); wandb-style telemetry (offline CSV only).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | MPS timing (18.6 ms/example, idle box) holds within ~2–3× under real load → N=2000 stays "minutes" | Summary / Pattern 4 | LOW — even 10× is 6 min; CPU fallback measured at 1.5 min |
| A2 | Ordinal-rank Spearman (no tie-averaging) is adequate for the D-05 convergence report | Code Example 6 | LOW — method string recorded in fisher_meta; exact ties in 13.9M fp32 squared-grads are rare |
| A3 | fp32 accumulation over 2000 additions of similar-magnitude `g²` terms introduces negligible error | Pattern 1 | LOW — standard numerical argument; statistics computed in fp64 regardless |
| A4 | Autocast type-promotion keeps the elementwise penalty in fp32 on the P100 fp16 fallback | Pattern 2 | LOW — primary path (MPS/CPU) has autocast disabled; fallback is optional and Phase 12's concern |

All other load-bearing claims were verified in-session (seam line numbers, dedup behavior,
test count, artifact existence, timing) or cited from the project's primary-source research.

## Open Questions

1. **Should the loop touch include `checkpoint_extra` threading for in-loop saves?**
   - What we know: the loop's in-loop `save_checkpoint` calls (Seam 3 best.pt / Seam 4a
     latest.pt) pass no `**extra` — so a Phase 12 EWC run killed mid-training produces a
     `latest.pt` **without** Fisher/θ*, and resume would depend on the sidecar cache
     (exactly ARCHITECTURE anti-pattern 2).
   - What's unclear: whether to solve it now (an additive `checkpoint_extra: dict | None = None`
     kwarg splatted into every `save_checkpoint` call — default `None` ≡ v1.0) or leave it to
     Phase 12's loop touch.
   - Recommendation: **include it in this phase's loop touch.** It is the same default-off
     additive discipline as `penalty_fn`, tested by the same bit-identity machinery, and it
     consolidates all v2.0 `loop.py` edits into the one phase whose success criteria already
     pin loop bit-preservation. Phase 10's own success criteria don't require it, so the
     planner may defer — but then Phase 12 re-opens `loop.py`. This sits adjacent to the
     user's loop-touch-scope discretion grant; the planner decides. (`extra_val_bins` +
     per-run CSV fieldnames: **defer to Phase 12** — retention telemetry has no consumer or
     test-in-anger until then.)

2. **Where does the Fisher-cache exporter/loader live?**
   - What we know: Phase 9's precedent puts schema-versioned, `weights_only=True`-safe
     exporters in `checkpoint.py` (`export_adapter`/`load_adapter`) with a locked dependency
     direction (checkpoint.py never imports the feature package; callers pass plain dicts).
   - What's unclear: `checkpoint.py` (`export_fisher`/`load_fisher`, symmetric precedent) vs
     `continual/fisher.py` (the artifact's owning package).
   - Recommendation: follow the precedent — `checkpoint.py`, plain-dict args,
     `FISHER_SCHEMA_VERSION`, structural validation in the loader. Either choice is defensible;
     pick one and mirror `load_adapter`'s error style.

3. **Smoke-script rerun semantics for the cache.**
   - What we know: `train_adapter_smoke.py` refuses to rerun a completed smoke (delete to
     redo). The Fisher run is <1 min and stateless.
   - Recommendation: refuse-if-cache-exists with a "delete to re-estimate" message (keeps the
     cache's provenance stable for Phase 12/13); the planner may instead choose
     overwrite-with-warning — both are fine.

## Environment Availability

All dependencies verified present in-session (2026-06-12):

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python venv (.venv) | all dev/test | ✓ | 3.11.15 | — |
| torch | Fisher/penalty/loop | ✓ | 2.7.1, MPS available | CPU (measured 1.5 min for N=2000) |
| numpy | window draws, stats | ✓ | 2.x (bundled with env) | — |
| pytest | tests | ✓ | collects 190 tests in 0.61 s | — |
| ruff (`make lint`) | CI/lint | ✓ | per Makefile | — |
| `checkpoints/best.pt` | anchor θ*, Fisher at the anchor | ✓ | 166.8 MB, 2026-06-05 | — (hard requirement; script raises FileNotFoundError like 09-04) |
| `data/train.bin` | Fisher window source | ✓ | 2.50 GB uint16 memmap | — |
| `data/val.bin` | (not needed by this phase; loop tests use fixtures) | ✓ | 25.3 MB | — |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x (installed in .venv) |
| Config file | none needed — house convention is bare `tests/` + `conftest.py` (exists) |
| Quick run command | `source .venv/bin/activate && pytest tests/test_fisher.py tests/test_ewc_penalty.py tests/test_loop_penalty_fn.py -q -x` |
| Full suite command | `source .venv/bin/activate && make test` (pytest -q; 190 existing tests must stay green) |

All tests CPU-only/GPU-free (house discipline); MPS proof lives in the smoke script, not the suite.

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EWC-01 | Per-example Fisher matches brute-force oracle on tiny fixture; differs from batched-gradient estimate | unit | `pytest tests/test_fisher.py -q -x` | ❌ Wave 0 |
| EWC-01 | Non-negativity, determinism (same seed ⇒ identical), batch-order invariance | unit | `pytest tests/test_fisher.py -q -x` | ❌ Wave 0 |
| EWC-01 | Mean-normalization: `mean(F)=1`, normalizer recorded, raw recoverable (D-01/D-02) | unit | `pytest tests/test_fisher.py -q -x` | ❌ Wave 0 |
| EWC-01 | Tied dedup: one entry per storage, `lm_head.weight` absent (data_ptr-pinned) | unit | `pytest tests/test_fisher.py -q -x` | ❌ Wave 0 |
| EWC-01 | RNG purity: global random/numpy/torch state bit-unchanged after `estimate_fisher` | unit | `pytest tests/test_fisher.py -q -x` | ❌ Wave 0 |
| EWC-01 | Fisher/θ*/λ/meta round-trip via `save_checkpoint(**extra)`/`load_checkpoint` | unit | `pytest tests/test_fisher_checkpoint.py -q -x` | ❌ Wave 0 |
| EWC-02 | Quadratic-form oracle vs hand-computed value; λ linearity; penalty gradient = λ·F·(θ−θ*) | unit | `pytest tests/test_ewc_penalty.py -q -x` | ❌ Wave 0 |
| EWC-02 | Penalty exactly 0.0 at the anchor (equality, not allclose) | unit | `pytest tests/test_ewc_penalty.py -q -x` | ❌ Wave 0 |
| EWC-02 | `penalty_fn=None` ≡ kwarg-omitted ≡ pre-edit golden trajectory (exact); zero-penalty fn ≡ None | unit | `pytest tests/test_loop_penalty_fn.py -q -x` | ❌ Wave 0 |
| EWC-02 | Penalty counted exactly once per optimizer step under grad accumulation (before `/accum`) | unit | `pytest tests/test_loop_penalty_fn.py -q -x` | ❌ Wave 0 |
| EWC-01 (real weights) | Fisher actually estimated at `best.pt` over TinyStories; convergence stats reported; cache written | smoke (manual-run, scripted SystemExit checks) | `python scripts/estimate_fisher_tinystories.py` (~1–2 min) | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** the quick run command above (new-phase test files, <30 s)
- **Per wave merge:** `make test` (full 190+ suite)
- **Phase gate:** full suite green + smoke script exit 0 before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_fisher.py` — covers EWC-01 unit behaviors
- [ ] `tests/test_ewc_penalty.py` — covers EWC-02 penalty behaviors
- [ ] `tests/test_loop_penalty_fn.py` — covers loop bit-identity + accum behaviors (the golden
      trajectory fixture must be captured **before** the loop edit — Pitfall 6)
- [ ] `tests/test_fisher_checkpoint.py` — covers the persistence seam (may merge into test_fisher.py)
- [ ] `scripts/estimate_fisher_tinystories.py` — the real-weights smoke + production cache
- Framework install: none — pytest already present

## Security Domain

`security_enforcement` is absent from config → treated as enabled. This phase has no network,
auth, or untrusted-input surface; the relevant categories are deserialization and artifact
hygiene.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes (artifact loading) | Schema-version + structural validation at the single load choke point (the `load_adapter` precedent) for the Fisher cache |
| V6 Cryptography | no | — |
| Deserialization safety | yes | Resume checkpoints: `weights_only=False` TRUSTED-ONLY (established posture, own files only). Fisher cache: tensors + primitives only → loads under `weights_only=True` — keep it that way (no dataclass instances or callables in the dict; `fisher_meta` is primitives) |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Pickle code-exec via `torch.load` of a foreign checkpoint | Tampering/Elevation | Trusted-own-files-only for `weights_only=False`; `weights_only=True` choke point for shareable artifacts (cache) |
| Supply chain | Tampering | Zero new dependencies in this phase — nothing to audit |
| Committed large/derived artifacts | Information disclosure / repo hygiene | `checkpoints/` and `logs/` already gitignored; cache lands there |

## Project Constraints (from CLAUDE.md)

Directives the planner must honor (extracted from `./CLAUDE.md`):

- **From-scratch boundary:** no HF transformers/PEFT model code; no `tiktoken`/HF tokenizers as
  implementation. Fisher/EWC via plain autograd only (no opacus, no torch.func — also D-03).
- **Primary training/dev = local M3/MPS, fp32, no AMP/GradScaler/torch.compile on MPS**;
  Kaggle P100 is optional fallback only. Fisher and all evals in fp32.
- **Python 3.11 venv MANDATORY** (dev box runs 3.14 — never validate against it); CI pins 3.11.
- **Tests CPU-only, GPU-free**; `make test` / `make lint` are the gates.
- **Offline only:** no wandb/online tooling; CSV + matplotlib telemetry.
- **Phase-1 layout discipline (D-11):** new module dirs added by their own phases — `continual/`
  is added by THIS phase; no other stub dirs.
- **Thin scripts, logic in the package**; `_REPO_ROOT` constants, no argparse (house D-04 pattern).
- **Never commit checkpoints/logs/tokens**; `.gitignore` covers them.
- **GSD workflow enforcement:** file changes go through GSD commands (this research is part of
  `/gsd:plan-phase`).
- **Reproducibility (QA-02):** seed + git SHA + config-embedded-in-checkpoint; RNG **state
  restore** on resume (never re-seed) — `estimate_fisher` must not perturb this contract.

## Sources

### Primary (HIGH confidence)
- Shipped code, line-verified this session: `src/personacore/training/loss.py` (the seam),
  `training/loop.py` (splice at 136–139, `_optimizer_step`, `train()` kwargs, CSV/RNG idioms),
  `checkpoint.py` (open-dict `**extra` reservation at line 77; `export_adapter`/`load_adapter`
  schema precedent), `training/data.py` (`get_batch_memmap` discipline; global `np.random`
  usage), `model/gpt.py` (LOCKED CE tail, tying at construction), `config.py`
  (ModelConfig/TrainConfig/RuntimeConfig), `seeding.py`, `scripts/train_adapter_smoke.py`
  (the 09-04 script shape), `tests/{test_assemble_loss,test_gpt_weight_tying,test_ablation_config,test_resume_curve}.py`
  (test idioms to mirror)
- In-venv empirical verification (2026-06-12): `named_parameters()` dedup (100 entries, tied
  tensor once) vs `state_dict()` (both keys, shared storage); fwd+bwd timing 18.6 ms/example
  MPS / 43.6 ms CPU at batch=1, block=256; Python 3.11.15, torch 2.7.1, MPS available; 190
  tests collected; `best.pt`/`train.bin`/`val.bin` present on disk
- `.planning/research/{SUMMARY,ARCHITECTURE,PITFALLS}.md` — the converged v2.0 research
  (Pattern 2, anti-patterns 2–4, Pitfalls 6–8), itself grounded in: van de Ven,
  *On the Computation of the Fisher Information in Continual Learning* (arXiv:2502.11756);
  Kirkpatrick et al. 2017 (PNAS); *EWC Nuts and Bolts* (arXiv:2105.04093)
- `.planning/phases/10-ewc-core/10-CONTEXT.md` — locked decisions D-01..D-05 + discretion grants

### Secondary (MEDIUM confidence)
- Autocast type-promotion behavior for elementwise ops (A4) — long-standing PyTorch AMP
  semantics, not re-verified against 2.7.1 docs this session (irrelevant on the primary
  MPS/CPU path where autocast is disabled)

### Tertiary (LOW confidence)
- None — no unverified WebSearch findings were used.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new deps; environment verified in-venv
- Architecture: HIGH — every seam re-verified line-by-line this session; the one genuinely new
  finding (in-loop saves don't carry `**extra` → Open Q1) is read directly from the code
- Pitfalls: HIGH — primary-source-grounded (van de Ven) plus two session-verified facts
  (named_parameters dedup; MPS-no-fp64) and one structural finding (fork_rng ≠ numpy isolation)

**Research date:** 2026-06-12
**Valid until:** ~2026-07-12 (stable domain — pinned torch, frozen v1.0 seams; revisit only if
loop.py/checkpoint.py change outside this phase)
