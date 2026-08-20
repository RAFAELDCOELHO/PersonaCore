# Stack Research — v4.0 Leakage Mitigation and Relearning Validation

**Domain:** From-scratch DP-SGD on LoRA gradients + adversarial extraction-aware training + relearning-attack harness, on PyTorch/MPS
**Researched:** 2026-08-20
**Confidence:** HIGH on the per-example-gradient cost and MPS behaviour (measured in this repo, this venv, production shapes). HIGH on the accountant formula (closed form cross-verified against an independent numerical oracle to 2e-13). MEDIUM on the utility prediction (signal-to-noise is an order-of-magnitude bound, not a forecast).

---

## TL;DR Prescription

> **Add nothing. Not one runtime dependency, not one dev dependency.** Every piece of v4.0 is
> already in `torch==2.7.1` + stdlib `math` + `numpy`. `opacus` is rejected even as a test oracle —
> see [What NOT to Use](#what-not-to-use).

Five measured findings that should drive roadmap decomposition:

1. **`torch.func.vmap(grad(functional_call(...)))` works on MPS in torch 2.7.1 and costs 1.02–1.07× a
   normal batched step** at B=8…64, production shape, numerically exact (per-example gradient-norm
   max relative error **6.5e-08** vs batch-1 autograd truth). Per-example gradients are effectively
   free here because the trainable surface is only 331,776 params — the extra work vs a batched step
   is just *not* reducing the weight gradient over the batch.
2. **The naive batch-1 loop costs 2.9–3.3×, not ~B×.** PROJECT.md's stated `~B×` (≈8×) assumption is
   wrong on this hardware — MPS is so far from saturated at B=8×T=256 that eight batch-1 passes cost
   about three batched passes. Either way it is superseded by (1).
3. **Ghost clipping is the wrong tool for LoRA and should be explicitly rejected**, not deferred.
   At r=8, T=256, the Goodfellow/ghost closed form costs ~33× *more* arithmetic than just
   materialising the per-example gradient. (Derivation in [Q1](#q1--per-example-gradient-computation).)
4. **Compute is not the binding constraint on the sweep; the corpus is.** A 200-step persona arm is
   ~17 s of MPS wall clock (83 ms/step at B=8). But `persona_real_train.bin` is 20,036 tokens = **78
   disjoint 256-token windows**, and `persona_persona_a` is **29**. At B=8 that is a sampling rate
   q = 0.10–0.28, so privacy amplification by subsampling is nearly gone, and the DP noise exceeds
   the clipping bound by a factor of σ·√d/B ≈ **72σ**. The lever that moves the frontier is
   **corpus size and lot size**, not step budget.
5. **`checkpoint.py` does not save MPS RNG state.** It saves `python`/`numpy`/`torch`(CPU)/`cuda`.
   DP-SGD's Gaussian draw would be the *first* consumer of device RNG in the training loop, so this
   latent gap becomes live in Phase 20. Verified fix available: `torch.Generator(device="mps")`
   `get_state()`/`set_state()` round-trips (44-byte uint8 tensor) and survives `torch.save`.

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **PyTorch** | `2.7.*` (venv runs **2.7.1**) — unchanged | Everything | `torch.func.vmap`/`grad`/`functional_call` are stable public API since 2.0 and **verified working on MPS in 2.7.1** (measured, not recalled). No API needed by v4.0 landed after 2.7. No version bump. |
| **`torch.func`** | ships in torch 2.7.1 | Per-example gradients | The whole DP-SGD hot path. `vmap(grad(f))` over the 72 LoRA tensors: **1.02–1.07× baseline cost**, exact. Composable transforms are a math primitive, not model code — same category as `F.scaled_dot_product_attention`, which the project already permits. |
| **stdlib `math`** | Python 3.11 | (ε, δ) accounting | `lgamma` + `log1p` + `exp` is the entire RDP accountant. ~30 lines. MPS has no fp64, so the accountant *must* live off-device in Python floats anyway — which makes the zero-dependency answer also the correct one. |
| **NumPy** | `~=2.4` — unchanged | Poisson subsampling index draw, quadrature oracle | `np.random.Generator.random(N) < q` is the Poisson-subsampling primitive. Also powers the accountant's independent numerical oracle (see below). |

### Supporting Libraries

**None.** No additions to `pyproject.toml` in any extra. The three things that would normally
pull a dependency are all covered:

| Need | Normally pulls | Covered by | Evidence |
|------|---------------|-----------|----------|
| Per-example gradients | `opacus` (GradSampleModule) | `torch.func.vmap(grad(...))` | measured 1.05×, rel err 6.5e-08 |
| RDP accounting | `opacus` / `dp-accounting` (→ `scipy`) | 30 lines of `math` | 3 independent oracles, best rel err 2e-13 |
| Accountant validation | `opacus` as test oracle | 1-D numerical quadrature in numpy + the q=1 closed form | see [Q5](#q5--is-any-dependency-warranted) |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| **pytest 9.x** — unchanged | Accountant oracles, per-example-gradient equivalence tests | All CPU-only. `vmap(grad(...))` equivalence vs batch-1 autograd runs fine on CPU at tiny shapes — no GPU-only skips added. |
| **ruff 0.15** — unchanged | Lint | — |
| **grep-guard test** (new, house pattern) | Structural enforcement | The v2.0 "structural enforcement replaces declared invariants" decision. See [Q5](#q5--is-any-dependency-warranted) for the exact guard, which here guards against a dependency that is *never added* — it pins the absence. |

## Installation

```bash
# No change. The v3.0 environment is the v4.0 environment.
source .venv/bin/activate
pip install -e ".[cpu,dev,demo]" --extra-index-url https://download.pytorch.org/whl/cpu
make test
```

Concretely: `pyproject.toml` `dependencies`, `[cpu]`, `[dev]`, `[demo]`, `[notebook]` are all
unchanged. The sha256-pinned close state carries forward untouched — v4.0 makes it four milestones
with zero new runtime dependencies, which is itself a portfolio claim worth keeping intact.

---

## Q1 — Per-example gradient computation

### Measured, this repo, this venv

Benchmark harness: real `GPT(ModelConfig())` (6 layers, n_embd=384, n_head=6, block_size=256,
vocab 8192) + real `inject_lora(m, LoRAConfig())` (r=8, six projections × six layers = 36
`LoRALinear`, **72 trainable tensors, 331,776 params**), `mark_only_lora_trainable`, MPS fp32,
torch 2.7.1, `torch.mps.synchronize()` around every timing region, warm-up excluded.

**Cost multiplier vs one ordinary batched forward+backward:**

| B | batched (baseline) | `vmap(grad)` | naive batch-1 | `vmap`/base | naive/base |
|---|---|---|---|---|---|
| 8 | 78.7 ms | 83.8 ms | 260.9 ms | **1.07×** | 3.31× |
| 16 | 168.8 ms | 178.5 ms | 511.8 ms | **1.06×** | 3.03× |
| 32 | 355.4 ms | 378.1 ms | 1028.4 ms | **1.06×** | 2.89× |
| 64 | 737.4 ms | 754.4 ms | 2188.5 ms | **1.02×** | 2.97× |

Both per-example columns include the full DP reduction (per-example norm → clip factor → weighted
sum), so these are step costs, not gradient-only costs. A separate run measured the tensor-hook +
`einsum` approach at **1.85×** (152.3 ms vs 82.2 ms) at B=8.

**Why `vmap` is nearly free, stated so the number is not mistaken for a fluke:** the base weights
are frozen (`requires_grad=False`), so the backward graph is identical in both cases and the FLOPs
are identical. The *only* extra cost of per-example gradients is declining to sum the weight
gradient over the batch — which materialises B copies of a **331,776**-param tensor: 10.6 MB at
B=8, 85 MB at B=64. That is the entire overhead. The multiplier would look completely different if
the base model were trainable; it is not, and will not be.

**Correctness (this is the part that must not be taken on faith):**

- `vmap(grad)` per-example gradient norms vs batch-1 `torch.autograd.grad` truth: **max relative
  error 6.55e-08** over 8 examples.
- Full per-tensor gradient for example 0, all 72 tensors: **max relative error 2.10e-06** (fp32 noise).
- Tensor-hook + `einsum` path: per-example norms **1.29e-07**; `sum_b` of hook grads vs
  `param.grad` from a normal `.backward()`: **A 2.46e-07, B 1.67e-07**.

### The four options, ranked

**1. `torch.func.vmap(grad(functional_call(...)))` — RECOMMENDED.**

```python
frozen = {n: p.detach() for n, p in model.named_parameters() if not p.requires_grad}
frozen.update({n: b.detach() for n, b in model.named_buffers()})

def loss_of(pdict, xi, yi):
    _, ls = functional_call(model, {**frozen, **pdict}, (xi.unsqueeze(0), yi.unsqueeze(0)))
    return ls

per_ex = vmap(grad(loss_of), in_dims=(None, 0, 0))(lora_params, x, y)  # dict of (B, *shape)
```

- **MPS:** works, exact. Verified on torch 2.7.1.
- **Cost:** 1.02–1.07×.
- **Module structure required:** none. It does not care that `lora_A`/`lora_B` are bare
  `nn.Parameter`s — `functional_call` swaps by *name*, and the LoRA names are already stable and
  already the artifact keys (`lora_state_dict`).
- **Constraints:** dropout > 0 in the vmapped region requires `randomness="different"` (measured;
  `randomness="error"` hard-raises). `LoRAConfig.dropout` defaults to `0.0`, so this is a landmine
  only if the adversarial arm turns it on.

**2. Tensor-hook + `einsum` closed form — the fallback, and worth building anyway as an oracle.**

Cost 1.85×, so it loses to `vmap` on speed. Its value is as a *second independent implementation* of
the same quantity, which is exactly the shape of evidence this project treats as load-bearing. It
also stays available if a future torch bump regresses MPS `vmap`.

**3. Naive batch-1 accumulation — the shape `estimate_fisher` already uses.** 2.9–3.3×. Correct,
trivially auditable, no functional-transform machinery. Best role: the *ground truth* the other two
are pinned against in the test suite (which is what it was used for above). Not the production path.

**4. Ghost clipping / the Goodfellow closed form — REJECT for this project, with arithmetic.**

Ghost clipping computes `‖G‖²_F = ⟨A Aᵀ, G Gᵀ⟩_F` at cost `O(T²(d_in + d_out))`, avoiding the
`O(T·d_in·d_out)` outer product. It wins when `T < d_in·d_out / (d_in + d_out)`. For `lora_A`
(d_in = 384, d_out = r = 8): the crossover is **T < 7.8 tokens**. The project runs **T = 256**.
Direct materialisation is `384·8·256 = 786K` vs ghost's `256²·392 = 25.7M` — ghost is **~33× more
arithmetic**. Ghost clipping exists because full fine-tuning has `d_in·d_out ≫ T²`; LoRA at rank 8
inverts that inequality. Rejecting it is a substantive, quantified design decision, not an omission.

### Does the closed form apply to `LoRALinear` "because it's pure `nn.Linear`"? — Partly. Verify this before planning around it.

**The premise as stated is false.** `src/personacore/lora/layer.py:41`:

```python
y = y + self.scale * (self.dropout(x) @ self.lora_A.T @ self.lora_B.T)
```

`lora_A` and `lora_B` are bare `nn.Parameter`s inside an inline matmul chain. They are **not**
`nn.Linear` submodules. Consequences:

- **`register_forward_hook` / `register_full_backward_hook` do not reach them.** A module hook on
  `LoRALinear` sees the wrapper's input `x` and output `y`; a hook on `self.base` sees the frozen
  layer. Neither gives you `dL/dh`, which is what the per-example gradient of `lora_A` needs. Any
  plan written as "hook the LoRA Linears" will not compile against this code.
- **The underlying *mathematical* structure is exactly a linear layer**, twice over, so the closed
  form is available — it just needs a **tensor** hook, not a module hook. Verified working:

```python
h     = self.dropout(x) @ self.lora_A.T   # (B, T, r)
delta = h @ self.lora_B.T                 # (B, T, out)
# per-example:  G_A[b] = (dL/dh[b])ᵀ @ x_drop[b]      -> (r, in)
#               G_B[b] = (dL/ddelta[b])ᵀ @ h[b]       -> (out, r)
h.register_hook(...); delta.register_hook(...)
G_A = torch.einsum("btr,bti->bri", gh, xd)
G_B = torch.einsum("bto,btr->bor", gd, h)
```

The `scale` factor needs no special handling: hooking `h` and `delta` yields grads that already
carry it through the chain. Verified `sum_b G_A == lora_A.grad` to 2.5e-07.

- **Restructuring `LoRALinear` to use `nn.Linear` submodules would break the artifact.** It renames
  `lora_A` → `lora_A.weight` in `state_dict()`, invalidating `persona_adapter.pt`, every v3.0
  checkpoint, `lora_state_dict`/`load_adapter_weights`, and the Phase-19 rank-1 component indexing.
  **Do not do this.** Tensor hooks get the same result with a zero-byte artifact diff — and `vmap`
  needs neither.

---

## Q2 — Privacy accounting

### Recommendation: hand-rolled RDP, Poisson-subsampled Gaussian, integer-α only, Balle conversion

**Why RDP and not the others:**

| Accountant | Hand-rollable? | Verdict |
|---|---|---|
| **RDP (Mironov 2017; Mironov–Talwar–Zhang 2019)** | **Yes — ~30 lines, stdlib `math`** | **USE THIS.** Integer α has an exact closed-form binomial sum. Composition over T steps is multiplication. |
| Moments accountant (Abadi et al. 2016) | Partly | Superseded. It *is* RDP in earlier clothing; the original implementation numerically integrated where MTZ later gave the closed form. No reason to reimplement the older, looser version. |
| PRV (Gopi–Lee–Wutschitz 2021) | **No** | Tighter (typically 10–20% lower ε), but needs FFT convolution of privacy-loss distributions with discretisation- and truncation-error control. That machinery *would* justify a dependency — and a subtly wrong hand-rolled PRV produces a **smaller** ε, i.e. it fails in the unsafe direction. Reject. |

**The formulas, exactly.** One Poisson-subsampled Gaussian step at sampling rate `q`, noise
multiplier `σ`, integer `α ≥ 2`:

```
log A_α = logsumexp_{i=0..α} [ log C(α,i) + i·log q + (α−i)·log(1−q) + (i² − i)/(2σ²) ]
RDP_α   = log A_α / (α − 1)
```

Composition over `T` identical steps: `RDP_α^total = T · RDP_α`. Conversion to (ε, δ):

```
ε(α) = RDP_α^total − (log δ + log α)/(α − 1) + log((α − 1)/α)
ε    = min over an α grid;  report the minimising α* alongside ε
```

The `log((α−1)/α)` and `log α` terms are the improved conversion (Balle et al. 2020, *Hypothesis
testing interpretations and Rényi differential privacy*), not the classic
`ε = RDP + log(1/δ)/(α−1)`. This is what Opacus uses; the classic form is looser but sound, so
using it is a conservative error, not a wrong one. Use the improved form and say which one you used.

**α grid:** `[2..16] ∪ {20,24,32,48,64,128,256,512,1024}`. Grid width matters — at the shapes
below, α* ran from 3 to 512. **If ε is minimised at the last grid point, the grid is truncating the
answer and ε is overstated.** That check belongs in the accountant, raising rather than returning.

### Verified — three independent oracles, all zero-dependency

The 30-line implementation was validated in-session:

1. **q = 1 collapses to the plain Gaussian mechanism**, whose RDP is *exactly* `α/(2σ²)`.
   Match to **< 1e-12 relative** at σ ∈ {0.5, 1, 2, 5} × α ∈ {2, 8, 32}. Closed-form limiting case,
   no external reference needed.
2. **Independent 1-D numerical quadrature.** The SGM's Rényi divergence reduces to a scalar problem:
   `D_α( (1−q)N(0,σ²) + q·N(1,σ²) ‖ N(0,σ²) )`. Trapezoid over a 4M-point grid, numpy only:

   | q | σ | α | closed form | quadrature | rel err |
   |---|---|---|---|---|---|
   | 0.01 | 1.1 | 4 | 0.0002667183 | 0.0002667183 | 2.0e-13 |
   | 0.05 | 2.0 | 8 | 0.0031215266 | 0.0031215266 | 1.2e-14 |
   | 0.2 | 1.5 | 3 | 0.0366592441 | 0.0366592441 | 2.5e-15 |
   | 0.001 | 0.8 | 16 | 5.1317277730 | 5.1317277730 | 1.7e-16 |
   | 0.5 | 3.0 | 5 | 0.0790885465 | 0.0790885465 | 5.1e-15 |

   This is a genuinely independent implementation (different mathematics, different failure modes),
   stronger than an oracle library that shares the same closed form.
3. **Small-q asymptotic** `RDP_α ≈ α·q²·(e^{1/σ²} − 1)/2`. At q = 1e-3, σ = 4, α = 3: closed form
   9.675e-08 vs asymptotic 9.674e-08. *(Note for whoever writes this test: the frequently-quoted
   `2q²α/σ²` is a 4× overstatement of the true leading term. Pinning against the wrong asymptotic is
   itself one of the plausible-but-wrong traps.)*

### Where a hand-rolled accountant produces a wrong-but-plausible ε — including the repo-specific ones

**T1 — Sampling assumption. LIVE IN THIS CODEBASE.** `training/data.py:85` (`get_batch_memmap`) and
`:117` (`get_batch_memmap_masked`) draw with `np.random.randint(0, len(data) − block_size − 1,
size=batch_size)` — **sampling with replacement, fixed lot size, over a continuum of start
offsets**. That is neither Poisson subsampling (independent inclusion, variable lot size) nor
shuffled fixed-size batches. Feeding `q = B/N` from this sampler into a Poisson-subsampled RDP
accountant is **unsound and yields a smaller ε than the mechanism earns.** The DP arm needs a new
`poisson_batch()` sibling in `training/data.py` over a fixed disjoint example index. Not optional.

**T2 — Overlapping windows destroy the record abstraction. LIVE IN THIS CODEBASE.** With
continuum start offsets, two "examples" one token apart share 255/256 of their content. DP's
neighbouring-datasets definition assumes records you can add or remove; here you cannot. The DP arm
must re-cut the persona corpus into a **fixed, disjoint, enumerated example set** and sample over
indices into it. This is a data-pipeline requirement, not an accountant detail.

**T3 — Gradient accumulation changes the lot.** `TrainConfig.grad_accum_steps` makes the effective
lot `batch_size × grad_accum_steps` while `_optimizer_step` performs one `optimizer.step()`. Two
ways to get this wrong: computing `q` from `batch_size` alone **understates q and gives a too-small
ε (unsound)**; adding Gaussian noise per micro-batch instead of once per optimizer step injects
`√accum ×` too much noise (sound but destroys utility, and the reported ε is then wrong in the
*conservative* direction, which is harder to notice). Pin `q = batch_size · grad_accum_steps / N`
and add noise exactly once, after the accumulation window.

**T4 — Loss reduction scale. LIVE IN THIS CODEBASE.** The model's CE tail reduces `mean` over
`B × T` tokens. A per-example gradient extracted from that batched loss is **1/B of** the true
per-example gradient. Measured: `hook_norms × B` matched batch-1 truth to 1.3e-07; without the `× B`
it is off by exactly 8. Getting this wrong silently changes what the clipping bound `C` means
relative to the noise `σ·C`, which changes utility without changing the reported ε — a plausible-
looking curve computed against a mis-scaled clip.

**T5 — Unit of privacy vs the claim being made. The biggest one for this milestone.** Example-level
DP bounds the influence of *one window*. The leakage claim from Phase 18 is about a *fact*. A fact
rendered into k windows needs **group privacy: roughly k·ε** (and δ blows up as
`k·e^{(k−1)ε}·δ`). At the current corpus, a single fact appears across a large share of the 78
windows, so a headline "ε = 1.6" that is quietly example-level could correspond to a fact-level
guarantee of no practical strength. Given v3.0 shipped an instrument-disagreement co-headline for
exactly this class of error, this must be decided and stated *before* the curve exists. Cleanest
resolution: **define one example = one fact rendering** and account at that granularity, so the ε
means what the gate reads it as meaning.

**T6 — The existing global clip after noising.** `_optimizer_step:165` calls
`torch.nn.utils.clip_grad_norm_(model.parameters(), train_cfg.grad_clip)` unconditionally. Applied
*after* DP noise it does **not** break ε — it is a data-independent function of an already-private
release, so post-processing immunity holds. It does silently rescale the noisy gradient and confound
the σ→utility reading. Disable it on the DP path and say so, rather than leaving a second clip
nobody accounts for.

**T7 — Fixed lot size reported as Poisson.** Even after switching to an index-based sampler, drawing
*exactly* B indices without replacement is sampling-without-replacement, which has its own (looser
in general) amplification analysis. Poisson subsampling means `mask = rng.random(N) < q`, accepting
a **variable** lot size — including, occasionally, an empty lot. Code that quietly resamples until
it gets exactly B examples has stopped being Poisson while still reporting Poisson ε.

**T8 — δ chosen relative to N.** Convention is `δ ≪ 1/N`. At N = 78, `δ = 1e-5` is fine; at N = 78
with `δ = 0.01` the guarantee is vacuous. Pin δ as a committed constant with its rationale, in the
same file as X and Y.

### What ε is actually reachable — computed at the real shape

`persona_real_train.bin` = 20,036 tokens = **78 disjoint 256-windows**. B=8, T=200 steps, δ=1e-5:

| unit of privacy | N | q | σ=1 | σ=2 | σ=4 | σ=8 | σ=16 | σ=32 |
|---|---|---|---|---|---|---|---|---|
| disjoint window (`persona_real`) | 78 | 0.103 | 11.50 | 3.78 | 1.60 | 0.73 | 0.34 | 0.17 |
| disjoint window (`persona_a`) | 29 | 0.276 | 34.70 | 11.61 | 4.80 | 2.15 | 1.00 | 0.47 |
| one fact rendering (est.) | 600 | 0.013 | 1.62 | 0.41 | 0.18 | 0.08 | 0.04 | 0.02 |
| corpus regenerated 10× | 780 | 0.010 | 1.40 | 0.33 | 0.14 | 0.06 | 0.03 | 0.01 |

σ required to hit a target ε (N=78, B=8, T=200, δ=1e-5): **ε≤10 → σ≥1.07; ε≤8 → σ≥1.23;
ε≤4 → σ≥1.92; ε≤2 → σ≥3.31; ε≤1 → σ≥6.06.** Cutting steps buys little (ε≤8 needs σ≥1.23 at T=200,
σ≥0.68 at T=10) — **step budget is the wrong knob**; N and B are the right ones.

**And the utility side, which is the actual risk.** Per-coordinate noise std is `σ·C/B`, so the
noise vector's norm is `σ·C·√d / B` against a signal bounded by `C`. With d = 331,776 (√d = 576) and
B = 8, the ratio is **72σ**. Even at σ = 1 the injected noise exceeds the entire clipping bound by
~72×. To bring that to O(1) you need `B ≈ σ·576` — which a 78-window corpus cannot supply at any
lot size.

*(Confidence: MEDIUM on the utility implication. The ratio is an isotropic-noise-vs-worst-case-signal
bound; AdamW's per-coordinate normalisation and the low effective dimension of the true gradient both
soften it in practice, and the true signal is usually well below C, which sharpens it. Treat it as
an order-of-magnitude planning number that says "grow N and B", not as a prediction of the curve.)*

**Roadmap consequence:** the DP arm's viability rests on **regenerating the persona corpus at 10–20×
with disjoint, enumerated examples**, and running large lots (B up to N, i.e. full-batch, since
q → 1 costs only the amplification the small N never had). Both are cheap — the corpus is
template-generated and a step is 83 ms. Neither is currently in scope, and both should be, ahead of
any sweep.

---

## Q3 — Existing PyTorch primitives vs what must be written

### Already available — use, do not rebuild

| Primitive | Role in v4.0 | Note |
|---|---|---|
| `torch.func.vmap` / `grad` / `functional_call` | Per-example gradients | The hot path. Works on MPS, torch 2.7.1. |
| `torch.Generator(device="mps")` | Reproducible noise stream | `get_state()`/`set_state()` verified round-tripping (44-byte uint8); survives `torch.save`. |
| `torch.autograd.grad` | Batch-1 ground truth in tests | Exactly the call `estimate_fisher` already makes. |
| `Tensor.register_hook` | Closed-form per-example grads (oracle / fallback) | Tensor-level, so no `LoRALinear` restructure. |
| `personacore.seeding.seed_everything` | Fresh-run seeding | `torch.manual_seed` **does** cover MPS — verified reproducible. No change needed for fresh runs. |
| `personacore.checkpoint` open-dict + `checkpoint_extra` | DP state persistence | Already open-dict; carrying `{sigma, C, q, steps_taken, accountant_state, noise_gen_state}` needs no schema change. |
| `personacore.lora.export_adapter` / `load_adapter` | Arm artifacts | Every sweep point ships as an adapter file, unchanged format. |
| `personacore.logging.CSVLogger` | Frontier curve data | Append `step,eps,sigma,clip,recall,extraction` — same offline-CSV posture. |
| `torch.nn.utils.clip_grad_norm_` | **Not reusable for DP** | It computes *one* global norm over a batch-reduced gradient. DP needs B norms over B gradients. It is the wrong primitive; see T6 for why leaving it enabled is also wrong. |

### Must be written from scratch (all small)

| Module | ~LOC | What |
|---|---|---|
| `privacy/accountant.py` | ~40 | Integer-α SGM RDP + Balle conversion + α-grid-truncation guard. Stdlib `math`. |
| `privacy/pergrad.py` | ~60 | `vmap(grad(functional_call))` over the LoRA surface; returns `{name: (B, *shape)}`; the `× B` reduction-scale correction (T4) lives here with a test. |
| `privacy/dpsgd.py` | ~80 | Per-example norm → clip factor `min(1, C/‖g‖)` → weighted sum → `+ N(0, (σC)²)` → `/B` → write into `param.grad`. |
| `training/data.py::poisson_batch` | ~30 | Poisson subsampling over a fixed disjoint example index (T1/T2/T7). |
| `data/` persona corpus regeneration | — | Disjoint, enumerated examples at 10–20× current size (see Q2). |
| `training/loop.py` gradient seam | ~10 | See below — **this is the one real architectural gap.** |

### The architectural gap the roadmap must plan for

**The EWC `penalty_fn` seam cannot carry DP-SGD.** `penalty_fn` adds a term to the *loss* before
`.backward()`. DP-SGD is not a loss term — it replaces the entire gradient-formation step:
per-example gradients, per-example clipping, noise, then averaging. Nothing in the current
`_optimizer_step` shape can express that.

Two additive options, both preserving the "bit-identical when off" discipline that got EWC accepted:

- **A: a `grad_fn=` parameter on `train()`** that replaces the `for micro in range(accum): ...
  backward()` block. `None` → today's code path, bit-for-bit. This mirrors `penalty_fn` exactly and
  is the house pattern.
- **B: a separate `dpsgd_train()`** in `privacy/`, reusing `schedule`, `CSVLogger`, `checkpoint`,
  `estimate_loss`. Zero risk to the v1.0/v2.0/v3.0 trajectory-equality golden fixtures — at the cost
  of duplicating the resume/logging/eval wiring, which is where drift bugs live.

**Recommend A.** The bit-identical-when-off golden-trajectory fixture already exists from Phase 10
and is exactly the test that makes A safe. B duplicates the most-tested code in the repo.

**Also required:** the **relearning harness** needs no new primitives at all — it is
`load_adapter(mitigated) → train(...) → phase18_extraction` on a step schedule, plus a
`fresh adapter` control arm at identical budget/seed. It reuses `teach_persona.py`'s arm machinery
wholesale. And the **adversarial arm** consumes `scripts/phase18_extraction.py`'s existing
`ATTACK_FAMILIES = ("A1-mild", "A1-aggressive", "A2", "A3")` and its dose axis directly as the
training-time intensity axis — the attack renderers (`apply_a1`, `build_a2_prompt`,
`build_a3_prompt`) are already parameterised by `dose`. **Neither of these two arms motivates a
single new dependency, and neither needs new stack research.**

---

## Q4 — MPS-specific breakage (all probed, torch 2.7.1)

| Probe | Result | Consequence |
|---|---|---|
| `torch.func.vmap(grad(functional_call))` on MPS | **WORKS**, exact (6.5e-08) | The recommendation stands. |
| `torch.Generator(device="mps")` + `manual_seed` | **WORKS**, reproducible | Use an explicit generator for DP noise. |
| `Generator.get_state()` / `set_state()` on MPS | **WORKS**, 44-byte uint8, round-trips | This is the resumability mechanism. |
| `torch.save` of that state tensor | **WORKS** | Drops into `checkpoint_extra` with no schema change. |
| **CPU `Generator` driving `torch.randn(device="mps")`** | **HARD FAILS** — `RuntimeError: Expected a 'mps' device type for generator but found 'cpu'` | You cannot reuse `loop.py`'s existing `torch.Generator(device="cpu")` for device-side noise. Either a device generator, or draw on CPU and `.to(device)`. |
| **`checkpoint.py` saves MPS RNG state** | **NO** — saves `python`/`numpy`/`torch`(CPU)/`cuda` only (`checkpoint.py:102-106`, `:138-143`) | **Concrete gap.** DP noise is the first device-RNG consumer in the training loop, so this latent hole goes live in Phase 20. Fix additively: carry the noise generator's own `get_state()`. |
| `torch.manual_seed` → `torch.randn(device="mps")` | reproducible | Fresh-run seeding is fine as-is. |
| **fp64 on MPS** | **UNSUPPORTED** — `TypeError: ... MPS framework doesn't support float64` | The accountant must run in Python floats on CPU. It does. `estimate_fisher` already documents this same constraint (`fisher.py:29`). |
| `vmap` + LoRA dropout > 0, `randomness="error"` | **HARD FAILS** | Landmine if the adversarial arm enables dropout. |
| `vmap` + LoRA dropout > 0, `randomness="different"` | **WORKS** | The correct setting; per-example dropout masks are also the semantically right thing under DP. |
| Noise draw cost, 331,776 coords, on-device MPS | **0.060 ms** = 0.07% of a step | Negligible. |
| Noise draw cost, CPU → MPS | **3.215 ms** = 3.87% of a step | 53× slower but still <4% of a step. |

**Noise-draw recommendation — pick deliberately, and record which:**

- **On-device `torch.Generator(device="mps")`** — 0.07% overhead, resumable via `get_state()`. But
  the noise stream is **device-specific**: the same seed will not reproduce the same adapter on CPU
  or on the Kaggle P100 fallback.
- **CPU-drawn then `.to(device)`** — 3.9% overhead (≈3.2 ms on an 83 ms step), and the same seed
  reproduces the **same weights on M3, CPU, and P100.**

**Recommend CPU-drawn.** This milestone's entire output is a set of arms whose comparability across
a frontier is the claim; 3.9% of 17 s per arm is 0.7 s, and device-independent regenerability is
worth more than that. It also means the accountant, the noise, and the tests all live in the same
device-free domain, and CI (CPU-only) exercises the *production* noise path rather than a proxy.

---

## Q5 — Is any dependency warranted?

**No. Reject `opacus`, including as a test-only oracle.** Stating the argument in full because the
milestone brief asked for it explicitly.

**What it would cost.** `opacus` 1.6.0 (current on PyPI, verified) declares core requirements
`numpy>=1.15`, `torch>=2.6.0`, `scipy>=1.2`, `opt-einsum>=3.3.0`. The torch pin is satisfied by
`2.7.*`, but **`scipy` and `opt-einsum` are new**, and `[dev]` extras install in CI, so this lands
`scipy` in the CPU-only GitHub Actions job — the heaviest wheel in the project, for a 30-line
function. `tiktoken~=0.13`, the precedent, is a single self-contained wheel with no scientific-stack
tail.

**What it would buy — and why that is less than it looks.** As an oracle, `opacus.accountants.
analysis.rdp` would confirm the closed form. But it implements **the same binomial formula**, so it
shares every failure mode: a transcription error in the exponent would be caught, a
misunderstanding of the *sampling assumption* would not — and the sampling assumption is where
this project's real risk is (T1/T2/T7 above are all live in the codebase; none of them is an
`opacus` disagreement, all of them are silent agreement on the wrong input).

**What replaces it, and is strictly stronger.** Three oracles, all zero-dependency, all shipped:

1. `q = 1` → plain Gaussian mechanism, `RDP_α = α/(2σ²)` **exactly**. A closed-form limiting case
   with no shared implementation lineage. Verified < 1e-12.
2. 1-D numerical quadrature of the Rényi divergence (numpy, already a core dependency). **Different
   mathematics, different failure modes** — the property an oracle is supposed to have and `opacus`
   does not. Verified to 2e-13.
3. Small-q asymptotic `α q²(e^{1/σ²} − 1)/2`. Verified to 4 significant figures.

Plus a fourth that no library provides: **the sampler itself must be pinned**, with a test asserting
`poisson_batch` produces variable lot sizes with mean `qN` and independent inclusion — the assumption
the ε rests on, and the one an accountant oracle structurally cannot check.

**If the argument were nonetheless overruled**, the discipline would be the `tiktoken` one, and it
would need all four parts, not just the first: (1) `opacus` in `[dev]` only, never in `dependencies`
or `[cpu]`; (2) imported only inside `tests/`, never under `src/` or `scripts/`; (3) an AST-walk
guard over `src/` + `scripts/` imports plus a fresh-interpreter probe asserting `opacus` never lands
in `sys.modules` after importing `personacore` — the exact mechanism `plot_phase15.py` already uses
for `torch`; (4) `Makefile:install`, `pyproject [dev]`, and `.github/workflows/ci.yml` moved
together, per the standing three-places rule in CLAUDE.md.

**Recommendation: do not take on that cost.** The zero-new-dependency streak is not sentiment — it
is the claim that this stack is genuinely hand-built, and it survives v4.0 intact.

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|---|---|---|
| `torch.func.vmap(grad)` | Naive batch-1 loop | If a torch upgrade regresses MPS `vmap`. Costs 2.9–3.3× — affordable at 83 ms/step. Keep it in the test suite as truth regardless. |
| `torch.func.vmap(grad)` | Tensor-hook + `einsum` | If `vmap` interacts badly with a future model change. 1.85×. Build it anyway as the second implementation. |
| Hand-rolled RDP | PRV accountant | Only if the frontier is genuinely ε-limited *and* a 10–20% tighter ε changes the gate verdict. At the shapes above the frontier is utility-limited, not accountant-limited. Revisit only if that flips. |
| CPU-drawn noise | On-device MPS generator | If the 3.9% step overhead ever matters. It does not at 17 s per arm. |
| `grad_fn=` seam in `train()` | Separate `dpsgd_train()` | If the golden-trajectory fixture proves too brittle to extend. Costs duplicated resume/logging/eval wiring. |
| Example = one fact rendering | Example = one 256-token window | Window-level is defensible **only** if the report states plainly that ε is window-level and gives the group-privacy factor for a fact. Do not leave it implicit. |
| Regenerate the persona corpus 10–20× | Keep the 78-window corpus | Keeping it means accepting q ≈ 0.1–0.28, near-zero amplification, and a noise/signal ratio of ~72σ. That is a legitimate published negative — but it should be a *chosen* result, not an unnoticed corpus artifact. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|---|---|---|
| **`opacus`** (any role, incl. test oracle) | Pulls `scipy` + `opt-einsum` into CPU-only CI; as an oracle it shares the closed form and therefore the failure modes; hand-rolling DP-SGD is the milestone's deliverable | Hand-rolled DP-SGD + 30-line RDP accountant + the three zero-dep oracles above |
| **`dp-accounting` / `prv_accountant` / `tensorflow-privacy`** | Same dependency tail (`scipy`, `absl`, `attrs`, `mpmath`); PRV's numerical machinery is the part you cannot hand-verify | Integer-α RDP |
| **`scipy`** | Would enter only via a DP library. The one place it is tempting — fractional-α RDP (needs `erfc`/`log_ndtr`) — is unnecessary: a wide integer-α grid is sound (integer α gives a *valid* RDP bound; a coarser grid only ever overstates ε) | Integer α only, wide grid, with a truncation guard |
| **Ghost clipping / Goodfellow closed form** | ~33× more arithmetic than direct materialisation at r=8, T=256; the crossover is T < 7.8 tokens | `vmap(grad)` (1.05×) or tensor-hook `einsum` (1.85×) |
| **Restructuring `LoRALinear` to hold `nn.Linear` submodules** | Renames `lora_A` → `lora_A.weight` in `state_dict()`, invalidating `persona_adapter.pt`, all v3.0 checkpoints, `lora_state_dict`/`load_adapter_weights`, and Phase 19's rank-1 component indexing | Tensor hooks (`h.register_hook`) — same math, zero artifact diff. Or `vmap`, which needs neither. |
| **`get_batch_memmap` as the DP sampler** | With-replacement draws over overlapping windows: not Poisson, not shuffled, and the records are not separable. Yields an ε smaller than the mechanism earns | A new `poisson_batch()` over a fixed disjoint example index |
| **Reusing `penalty_fn` for DP-SGD** | It is a loss seam. DP-SGD replaces gradient formation, not the loss | A `grad_fn=` seam, `None`-default, bit-identical when off |
| **Leaving `clip_grad_norm_` enabled on the DP path** | Does not break ε (post-processing), but silently rescales the noised gradient and confounds every σ→utility reading | Disable on the DP path; record that it was disabled |
| **`torch.compile`** on the DP path | Unchanged from v1.0 — immature Apple codegen, and `vmap` composition adds a second fragile layer for no gain at 83 ms/step | Eager |
| **fp16/bf16 anywhere in DP-SGD** | Squared per-example gradient norms underflow in fp16, exactly the reason `estimate_fisher` is fp32-only. MPS has no AMP path regardless | fp32 |
| **Bumping torch past 2.7 for v4.0** | Nothing v4.0 needs landed after 2.7. A bump risks the Pascal wheel constraint on the dormant P100 fallback for zero benefit | `torch==2.7.*` |
| **A step-budget-driven sweep design** | ε barely moves with T (σ≥1.23 at T=200 vs σ≥0.68 at T=10) while utility collapses. Step budget is the wrong axis | Sweep σ; move N and B as design parameters |

---

## Stack Patterns by Variant

**DP-SGD arm (Phase 20+):**
- `poisson_batch()` over a fixed disjoint example index → `vmap(grad(functional_call))` over the 72
  LoRA tensors → per-example norms (`× B` reduction correction) → clip to C → sum → add
  `N(0, (σC)²)` from a CPU generator → `/lot_size` → write to `param.grad` → `optimizer.step()`.
- **No** `clip_grad_norm_`. **No** `penalty_fn` (EWC is a separate axis; if both run, the penalty is
  a *loss* term inside the per-example loss and its sensitivity must be argued, not assumed).
- Checkpoint carries `{sigma, clip_C, q, lot_size, steps_taken, delta, alpha_grid, eps_so_far,
  alpha_star, noise_gen_state}` in `checkpoint_extra`.
- Accountant runs on CPU in Python floats, called once per checkpoint, not per step.

**Adversarial extraction-aware arm (Phase 20+):**
- No new stack. Reuses `phase18_extraction.ATTACK_FAMILIES` + its `dose` axis as the training-time
  intensity axis; `apply_a1` / `build_a2_prompt` / `build_a3_prompt` are already dose-parameterised.
- Plain `train()` — no gradient seam, no accountant, no per-example anything. Explicitly **no formal
  guarantee**; generalisation to unseen attacks is the declared open question.

**Relearning harness (Phase 20+):**
- No new stack. `load_adapter(mitigated_arm)` → `train()` on a step schedule → score with the
  Phase-18 pipeline at each checkpoint → against a `fresh adapter` control at identical budget and
  seed protocol. Two instruments: absolute recovery ceiling (the gate) and cost-to-recovery (the
  qualifier).

**Unmitigated control arm:**
- Identical to Phase 14's `teach_persona.py` path at the v4.0 budget/seed protocol. If the corpus is
  regenerated (recommended), **the control must be retrained on the regenerated corpus** — otherwise
  the frontier compares against a baseline trained on different data, which is precisely the
  run-to-run confound the milestone already ruled out for v2.0's published numbers.

**If MPS `vmap` regresses on a future torch:**
- Fall back to the tensor-hook `einsum` path (1.85×) or the batch-1 loop (2.9–3.3×). Both are
  already in the test suite as equivalence oracles, so the fallback is a one-line switch, not a port.

---

## Version Compatibility

| Package A | Compatible With | Notes |
|---|---|---|
| `torch` 2.7.1 (venv, verified) | `torch.func.vmap`/`grad`/`functional_call` on **MPS** | Measured working and exact this session. Public stable API since 2.0. Nothing v4.0 needs landed after 2.7. |
| `torch` 2.7.1 | `torch.Generator(device="mps")` + `get_state`/`set_state` | Verified round-tripping, 44-byte uint8, `torch.save`-able. |
| MPS backend | **no fp64** | Accountant stays in Python floats on CPU. Same constraint `estimate_fisher` already documents. |
| MPS backend | **no fp16 AMP** | Unchanged from v1.0. DP-SGD is fp32 regardless — squared per-example grad norms underflow in fp16. |
| `vmap` | `nn.Dropout(p>0)` | Requires `randomness="different"`; `randomness="error"` hard-raises. `LoRAConfig.dropout` defaults to 0.0. |
| `numpy ~=2.4` | Poisson subsampling + quadrature oracle | Already a core dependency. |
| P100 fallback (dormant) | unchanged | `cu126`-or-earlier Pascal constraint stands. Nothing in v4.0 changes it; nothing in v4.0 requires it. |
| `pyproject.toml` | **unchanged** | Zero additions in `dependencies`, `[cpu]`, `[dev]`, `[demo]`, `[notebook]`. |

---

## Sources

- **Measured in-repo, this session** (HIGHEST confidence — production shapes, `.venv` torch 2.7.1,
  MPS, `torch.mps.synchronize()`-fenced timings): per-example gradient cost multipliers at B=8/16/32/64;
  `vmap`-vs-batch-1 numerical equivalence (6.5e-08); tensor-hook closed-form equivalence (2.5e-07);
  MPS Generator state round-trip; CPU-generator-on-MPS failure; MPS fp64 failure; `vmap`+dropout
  randomness modes; noise-draw costs; RDP accountant vs three oracles; persona corpus window counts;
  ε tables and σ-for-target-ε solves.
- **In-repo source read** (HIGH): `src/personacore/lora/layer.py:38-42` (inline matmul, bare
  `nn.Parameter`); `src/personacore/training/loop.py:136-169` (`_optimizer_step` ordering, the
  unconditional `clip_grad_norm_`); `src/personacore/training/data.py:65,85,117`
  (`np.random.randint` with-replacement sampling); `src/personacore/checkpoint.py:102-106,138-143`
  (RNG slots — no MPS); `src/personacore/continual/fisher.py` (batch-1 loop precedent, fp64-on-MPS
  note); `scripts/phase18_extraction.py:146` (`ATTACK_FAMILIES`, dose axis); `scripts/teach_persona.py`
  (B=8, 200 steps, LR 3e-4, wd 0.0); `pyproject.toml` (current pins).
- https://arxiv.org/abs/1908.10530 — Mironov, Talwar, Zhang, *Rényi Differential Privacy of the
  Sampled Gaussian Mechanism* (2019). The integer-α closed form and the Poisson-subsampling
  assumption. (HIGH)
- https://github.com/pytorch/opacus (`opacus/accountants/analysis/rdp.py`) — independent confirmation
  of the exact integer-α log-A formula `Σ_i log C(α,i) + i·log q + (α−i)·log(1−q) + (i²−i)/(2σ²)` and
  the conversion `ε = RDP − (log δ + log α)/(α−1) + log((α−1)/α)`; also the confirmation that the
  fractional-α path is what requires `scipy.special.erfc`/`log_ndtr`. Read as a reference, **not
  adopted as a dependency.** (HIGH)
- https://pypi.org/pypi/opacus/json — opacus 1.6.0 core requirements: `numpy>=1.15`, `torch>=2.6.0`,
  `scipy>=1.2`, `opt-einsum>=3.3.0`. The concrete dependency cost. (HIGH)
- Balle, Barthe, Gaboardi, Hsu, Sato, *Hypothesis testing interpretations and Rényi differential
  privacy* (AISTATS 2020) — the improved RDP→(ε,δ) conversion. (MEDIUM — formula verified via the
  Opacus implementation above rather than read from the paper directly.)
- Abadi et al., *Deep Learning with Differential Privacy* (CCS 2016) — the moments accountant and
  DP-SGD's per-example clip + Gaussian noise structure. (MEDIUM — background; superseded operationally
  by the MTZ closed form.)
- https://pytorch.org/blog/clipping-in-opacus/ — Fast Gradient Clipping and Ghost Clipping: the
  Goodfellow trick's restriction to fully-connected layers and Li et al.'s sequential-input
  generalisation. Confirms the mechanism whose cost model is rejected above. (HIGH)
- https://arxiv.org/html/2502.05374v1 — *Towards LLM Unlearning Resilient to Relearning Attacks*;
  and https://arxiv.org/html/2409.18025v3 — *An Adversarial Perspective on Machine Unlearning for AI
  Safety*. Both corroborate the relearning-attack framing and the specific failure mode this
  milestone is designed to catch: forgotten content resurfacing after a *single epoch* on a few
  forget samples, i.e. suppression masquerading as removal. (MEDIUM — WebSearch summaries, framing
  only; no numeric claim taken from them.)
- https://arxiv.org/pdf/2506.00688 — *Existing LLM Unlearning Evaluations Are Inconclusive*: the two
  assumptions relearning-based evaluation rests on (relearning must not generalise from retain data;
  the evaluator must know the unlearning data format). Directly relevant to the fresh-adapter control
  design. (MEDIUM — WebSearch summary.)

### Open / unverified

- **Evaluation wall-clock is unmeasured.** A generation-throughput probe failed to produce usable
  timings this session and no number is asserted. This matters: training is ~17 s per arm, so if the
  Phase-18 precedent of 42,480 draws per arm costs materially more than that, **the sweep budget Z is
  gated by evaluation, not by DP-SGD cost** — which inverts the milestone brief's stated assumption.
  The Phase-20 cost calibration should measure *both* legs, and the resource-budget pre-registration
  should be written against the larger one.
- **The 72σ noise/signal ratio is a bound, not a forecast** (MEDIUM). AdamW per-coordinate
  normalisation and the true gradient's low effective dimension both soften it; the true signal
  sitting well below C sharpens it. It justifies "grow N and B before sweeping"; it does not predict
  where the frontier lands.
- **The fact-rendering count (~600) in the ε table is an estimate**, not a corpus measurement. It
  should be replaced with the real count once the regenerated corpus exists.

---
*Stack research for: from-scratch DP-SGD + adversarial training + relearning validation on PyTorch/MPS*
*Researched: 2026-08-20*
