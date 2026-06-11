# Phase 4: GPT Transformer Decoder - Research

**Researched:** 2026-06-05
**Domain:** From-scratch GPT-2-style transformer decoder in pure PyTorch (causal MHA, pre-norm blocks, weight tying, GPT-2 init), gated by silent-bug unit tests
**Confidence:** HIGH

## Summary

Phase 4 implements the central "I built a transformer" artifact: a ~13.9M-parameter GPT-2-faithful decoder built by hand in `src/personacore/model/gpt.py`, honoring the **already-locked** `forward(idx, targets=None) -> (logits, loss)` contract so it drops into the proven Phase-3 training loop with **zero** harness changes. Every consequential decision is already locked in `04-CONTEXT.md` (D-01..D-11): the architecture is canonical GPT-2/nanoGPT (pre-norm, learned positional embeddings, GELU-tanh MLP, weight-tied head, GPT-2 residual-scaled init), and the from-scratch boundary is precise — hand-roll attention and LayerNorm with `F.scaled_dot_product_attention` and `nn.LayerNorm` as **test-only equivalence oracles**, while GELU may use `F.gelu`.

This research is therefore **implementation-focused, not exploratory**: it does not re-decide anything. It pins down the exact mechanics the planner needs to write correct tasks and tests for the six MODEL requirements — the GPT-2 per-tensor init recipe with the `0.02/sqrt(2·n_layer)` residual scaling applied to **both** `c_proj` and `fc_out` (D-04a), the `data_ptr()` weight-tying mechanism and ordering, the causality-perturbation test design that guards the mask-before-softmax bug, the manual-vs-sdpa numerical equivalence harness, the hand-rolled-LayerNorm-vs-`nn.LayerNorm` oracle, and the autocast-safety rules that keep the fp16 loop path working untouched. All claims are grounded in the existing codebase contracts and the canonical GPT-2/nanoGPT reference architecture, which is stable and unchanged across PyTorch 2.x.

**Primary recommendation:** Build `GPT(ModelConfig)` as a hand-rolled GPT-2 decoder with six named `nn.Linear` projections per block (`q_proj/k_proj/v_proj/c_proj/fc_in/fc_out`), hand-rolled `LayerNorm`, an `attn_impl="manual"` default toggle, a non-persistent lower-triangular causal buffer, weight tying via `self.lm_head.weight = self.wte.weight` set **after** init, and a `_init_weights` pass that applies `0.02/sqrt(2·n_layer)` std to `c_proj`+`fc_out` and `0.02` everywhere else. Gate it with the five MODEL test families mirroring the Phase-3 test style (`tests/test_*.py`, CPU-only, `seed_everything`/`torch.manual_seed`, `torch.allclose`).

## Architectural Responsibility Map

This is a single-tier, on-device ML library — there is no client/server/CDN/DB split. The relevant "tiers" are the **from-scratch boundary** layers: what the model owns vs. what the (untouched) training harness owns vs. what PyTorch primitives provide.

| Capability | Primary Owner | Secondary | Rationale |
|------------|--------------|-----------|-----------|
| Transformer math (attention, MLP, blocks) | `model/gpt.py` (hand-rolled) | PyTorch `nn`/`F` primitives | The from-scratch portfolio claim lives here (D-01, D-08, D-09) |
| LayerNorm math | `model/gpt.py` (hand-rolled) | `nn.LayerNorm` as test oracle (D-09) | Narrative shows normalization math; oracle proves correctness |
| GELU activation | `F.gelu(approximate="tanh")` | — | Pure pointwise primitive; hand-rolling adds no narrative (D-09) |
| Causal mask | `model/gpt.py` (non-persistent buffer) | `is_causal=True` in sdpa path | Both paths share the causality contract (D-02a) |
| Weight init recipe | `model/gpt.py` `_init_weights` | — | GPT-2 init is part of the architecture claim (MODEL-04) |
| Loss assembly (CE) | model returns base CE; `training/loss.py` owns `assemble_loss` | — | Model stays PURE — EWC seam stays in `training/` (D-05) |
| Optimizer / LR / AMP / checkpoint / data | `training/` (reused UNTOUCHED) | — | Phase-3 harness is proven; Phase 4 swaps only the model (D-07) |
| Sampling / `generate` | `training/loop.py::sample` (exists) / Phase 6 | — | Model has NO `generate` method this phase (D-05) |
| Device / precision / autocast | `RuntimeConfig` (single source of truth) | — | Model must be autocast-safe, never call `torch.cuda.*` |

**Load-bearing tier rule:** the model is a pure `(logits, loss)` producer. It must not import from `training/`, must not assemble loss beyond base CE, must not implement `generate`, and must not call `torch.cuda.*` or do manual dtype casting. Any task that puts loss-assembly, sampling, or device logic inside `gpt.py` is mis-tiered.

## Standard Stack

This phase installs **no new packages**. It uses only PyTorch primitives already pinned by the project (`torch`, plus `pytest` for tests) — all present from Phases 1–3. There is therefore **no Package Legitimacy Audit** (no external dependency is added). This is a from-scratch ML implementation phase, not a framework-integration phase.

### Core (already present — no install)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `torch` | Kaggle pre-installed / local `2.7.*` CPU | `nn.Module`, `nn.Linear`, `nn.Embedding`, `F.softmax`, `F.gelu`, `F.scaled_dot_product_attention`, `nn.LayerNorm` (oracle) | The only allowed DL framework; HF transformers/PEFT excluded by design (CLAUDE.md) [CITED: ./CLAUDE.md] |
| `pytest` | `~=9.0` | All MODEL gates, CPU-only | First-class deliverable; Phase-3 test idiom [VERIFIED: pyproject.toml] |

### What this phase does NOT add
| Avoid | Why | Use Instead |
|-------|-----|-------------|
| HF `transformers` `GPT2Model` / `GPT2Block` | Excluded by design — the portfolio value is the hand-built transformer | Own `nn.Module` blocks (D-08, CLAUDE.md) |
| HF `peft` / any LoRA wrapper | Out of M1 scope entirely; Phase 4 leaves only the *named-module* seam (MODEL-07) | Named `nn.Linear` modules only, no wrapper (D-03/D-04) |
| `flash-attn` pip package | Doesn't support Pascal; the sdpa math backend already covers the equivalence test | `F.scaled_dot_product_attention(is_causal=True)` (math backend) [CITED: ./CLAUDE.md] |

**Installation:** None. `import torch` only. (Verification of torch version is a Phase-1/Phase-5 concern; Phase-4 tests run CPU-only where the Pascal wheel constraint is irrelevant.)

## Architecture Patterns

### System Architecture Diagram

Data flow for one forward pass (`forward(idx, targets) -> (logits, loss)`), all owned by `gpt.py` except where noted:

```
idx (B,T) int64
   │
   ├─► wte: nn.Embedding(vocab=8192, n_embd=384)  ──► tok_emb (B,T,C)
   │
   └─► positions arange(T) ─► wpe: nn.Embedding(block_size=256, n_embd=384) ─► pos_emb (1,T,C)
                                              │
              tok_emb + pos_emb ─► (optional dropout=0.0) ─► x (B,T,C)
                                              │
            ┌─────────────────────────────────┴── × n_layer (6) Blocks (pre-norm) ──┐
            │  x ─► ln_1 (hand-rolled LayerNorm) ─► CausalSelfAttention ─┐           │
            │                                                            ├─(+)─► x   │  residual 1
            │  x ───────────────────────────────────────────────────────┘           │
            │  x ─► ln_2 (hand-rolled LayerNorm) ─► MLP(fc_in→GELU→fc_out) ─┐         │
            │                                                              ├─(+)─► x  │  residual 2
            │  x ────────────────────────────────────────────────────────┘          │
            └────────────────────────────────────────────────────────────────────────┘
                                              │
                                  ln_f (hand-rolled LayerNorm) ─► x (B,T,C)
                                              │
                              lm_head: nn.Linear(C, vocab, bias=?) ─► logits (B,T,V)
                              (lm_head.weight IS wte.weight — shared tensor, data_ptr identical)
                                              │
                          ┌───────────────────┴───────────────────┐
                  targets is None                          targets given
                          │                                       │
                  return (logits, None)        loss = F.cross_entropy(
                  (sampling path)                  logits.view(B*T, V), targets.view(B*T))
                                               return (logits, loss)   ← IDENTICAL flatten to bigram.py:37-38
                                                          │
                            [training/loop.py — UNTOUCHED] assemble_loss(base_loss, ()) ─► optimizer step
```

CausalSelfAttention internals (the from-scratch centerpiece, D-01):

```
x (B,T,C)
  ├─ q_proj ─► q ─┐
  ├─ k_proj ─► k ─┤ each reshape (B,T,C) -> (B, n_head, T, d_head=C/n_head=64)
  └─ v_proj ─► v ─┘
                 │
   attn_impl == "manual" (DEFAULT):           attn_impl == "sdpa":
     att = q @ k.transpose(-2,-1) / sqrt(d_head)    y = F.scaled_dot_product_attention(
     att = att.masked_fill(tril[:T,:T]==0, -inf)        q, k, v, is_causal=True,
     att = softmax(att, dim=-1)                          dropout_p=0.0)
     att = dropout(att)                              # math backend on Pascal/CPU
     y = att @ v                              # equivalence test: allclose(manual, sdpa, atol≈1e-5)
                 │
   y reshape (B, n_head, T, d_head) -> (B,T,C)
   y = c_proj(y)  ─► (residual-scaled init)
   y = dropout(y)
```

### Recommended Project Structure
```
src/personacore/model/
├── __init__.py     # add: from .gpt import GPT ; __all__ += ["GPT"]  (mirror existing bigram export)
├── bigram.py       # UNTOUCHED — Phase-3 baseline + the contract analog
└── gpt.py          # NEW — GPT, Block, CausalSelfAttention, MLP, LayerNorm (one file, nanoGPT-style)
```
nanoGPT keeps the whole decoder in one `model.py`; a single `gpt.py` matches the existing `bigram.py` layout and the "thin entry points, logic in package" rule. Splitting into submodules adds nothing at this scale.

### Pattern 1: Module construction order (init → tie → init-pass)
**What:** Build all modules, then tie weights, then run the GPT-2 init pass. Ordering matters for both correctness and the `data_ptr()` test.
**When to use:** Always, in `GPT.__init__`.
**Example:**
```python
# Source: nanoGPT model.py GPT.__init__ pattern (conceptual reference; hand-implemented). [ASSUMED]
class GPT(nn.Module):
    def __init__(self, config: ModelConfig, attn_impl: str = "manual"):
        super().__init__()
        self.config = config
        self.wte = nn.Embedding(config.vocab_size, config.n_embd)      # token emb
        self.wpe = nn.Embedding(config.block_size, config.n_embd)      # learned positional emb
        self.drop = nn.Dropout(config.dropout)
        self.blocks = nn.ModuleList(Block(config, attn_impl) for _ in range(config.n_layer))
        self.ln_f = LayerNorm(config.n_embd)                          # hand-rolled
        self.lm_head = nn.Linear(config.n_embd, config.vocab_size, bias=False)

        # 1) GPT-2 init pass over ALL params (named-aware for residual scaling)
        self.apply(self._init_weights)
        for name, p in self.named_parameters():
            if name.endswith("c_proj.weight") or name.endswith("fc_out.weight"):
                torch.nn.init.normal_(p, mean=0.0, std=0.02 / math.sqrt(2 * config.n_layer))

        # 2) WEIGHT TYING — do this AFTER init so the shared tensor isn't re-initialized twice.
        self.lm_head.weight = self.wte.weight   # share the SAME nn.Parameter (data_ptr identical)
```
**Critical ordering note:** nanoGPT sets `self.transformer.wte.weight = self.lm_head.weight` (head→emb). Either direction yields a shared tensor, but the assignment must happen **after** `self.apply(self._init_weights)`, otherwise the embedding gets initialized, then the head gets initialized, and (because they're the same object after tying) the second init wins — which is fine numerically only if both use the same std. Tying **after** init avoids any ambiguity: the surviving tensor is the embedding init (std 0.02), and `lm_head` is never separately initialized. (The standard GPT-2 head has `bias=False`; keep it so the tied weight is the only head parameter.)

### Pattern 2: Per-tensor GPT-2 init recipe (`_init_weights`) — MODEL-04
**What:** Module-type-dispatched init applied via `self.apply`.
**Example:**
```python
# GPT-2 init recipe (canonical; matches HF GPT2 and nanoGPT). [ASSUMED — verify std targets in test]
def _init_weights(self, module):
    if isinstance(module, nn.Linear):
        torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
        if module.bias is not None:
            torch.nn.init.zeros_(module.bias)          # biases ON (D-08), zero-init
    elif isinstance(module, nn.Embedding):
        torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
    # hand-rolled LayerNorm: weight=1, bias=0 set in its own __init__ (see Pattern 4)
```
**Per-tensor init-std target table** (what the MODEL-04 test asserts; `n_layer=6` → `0.02/sqrt(12) ≈ 0.005774`):

| Tensor (named-param suffix) | Init | Target std | Mean |
|---|---|---|---|
| `wte.weight` (token emb, also the tied head) | normal | 0.02 | 0 |
| `wpe.weight` (positional emb) | normal | 0.02 | 0 |
| `q_proj.weight`, `k_proj.weight`, `v_proj.weight` | normal | 0.02 | 0 |
| `fc_in.weight` | normal | 0.02 | 0 |
| **`c_proj.weight`** (attn output → residual) | normal | **0.02/√(2·6) ≈ 0.005774** | 0 |
| **`fc_out.weight`** (MLP output → residual) | normal | **0.02/√(2·6) ≈ 0.005774** | 0 |
| all `*.bias` (Linear + LayerNorm) | zeros | 0.0 (exact) | 0 |
| LayerNorm `weight` (ln_1/ln_2/ln_f) | ones | n/a (assert all == 1) | 1 |

**D-04a is the single most error-prone fact:** the residual-scaled std applies to **BOTH** output projections (`c_proj` AND `fc_out`), not just `c_proj`. The roadmap phrases it as "residual-scaled `c_proj`" but with HF naming that means both residual-stream writers. A test that only checks `c_proj` would silently pass a model that mis-inits `fc_out`.

### Pattern 3: Causal mask buffer (D-02a)
**What:** A registered non-persistent lower-triangular buffer sized to `block_size`, sliced `[:T,:T]` each forward.
**Example:**
```python
# In CausalSelfAttention.__init__:
self.register_buffer(
    "tril",
    torch.tril(torch.ones(config.block_size, config.block_size)).view(
        1, 1, config.block_size, config.block_size),
    persistent=False,   # NOT saved in state_dict — it's a derived constant, regenerated on load
)
# In manual forward (mask applied BEFORE softmax):
att = att.masked_fill(self.tril[:, :, :T, :T] == 0, float("-inf"))
att = F.softmax(att, dim=-1)
```
`persistent=False` keeps the mask out of the checkpoint (it's a pure function of `block_size`) and out of `data_ptr`/param-count concerns. The slice `[:T,:T]` lets the model accept any `T <= block_size`.

### Pattern 4: Hand-rolled LayerNorm with `nn.LayerNorm` oracle (D-09)
**What:** Implement LayerNorm math by hand; test against `nn.LayerNorm` for equivalence.
**Example:**
```python
# Hand-rolled LayerNorm (the from-scratch normalization narrative, D-09). [ASSUMED]
class LayerNorm(nn.Module):
    def __init__(self, ndim: int, eps: float = 1e-5):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(ndim))   # gamma init 1
        self.bias = nn.Parameter(torch.zeros(ndim))     # beta init 0
        self.eps = eps
    def forward(self, x):
        mean = x.mean(dim=-1, keepdim=True)
        var = x.var(dim=-1, keepdim=True, unbiased=False)   # population var (matches nn.LayerNorm)
        return (x - mean) / torch.sqrt(var + self.eps) * self.weight + self.bias
```
**Equivalence oracle subtlety:** `nn.LayerNorm` uses **biased/population** variance (`unbiased=False`) with the same `eps=1e-5` default. The hand-rolled version MUST use `unbiased=False` or the equivalence test fails at the ~1e-3 level. Assert `torch.allclose(custom(x), nn.LayerNorm(C)(x), atol=1e-6)` after copying the (trivial) weight=1/bias=0 params (they match by default init, so no copy needed when both are fresh). Use a random `x` of shape `(B,T,C)` in fp32.

### Anti-Patterns to Avoid
- **Fused `c_attn` QKV projection:** D-03 explicitly forbids it — use three separate `q_proj/k_proj/v_proj` so M2 LoRA can target Q/V and freeze K per-module. A fused projection breaks the MODEL-07 seam.
- **Mask applied AFTER softmax (or via additive bias added after normalization):** the whole point of MODEL-06. Mask must be `masked_fill(-inf)` **before** `softmax`. Applying it after lets probability leak from future tokens.
- **Manual `.half()`/`.float()` inside the model:** breaks autocast. Let `RuntimeConfig.autocast()` own dtype (see Autocast-Safety below).
- **`generate`/`sample`/`assemble_loss` inside `gpt.py`:** the model stays pure (D-05). Sampling already lives in `training/loop.py::sample`.
- **`bias=True` on `lm_head`:** standard GPT-2 head is bias-free; a head bias would be a second, untied head parameter that complicates the count-once test.
- **Saving the causal buffer in the checkpoint:** use `persistent=False`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Reference attention for the equivalence test | A second by-hand "reference" | `F.scaled_dot_product_attention(is_causal=True)` | It IS the allowed reference primitive (D-01); math backend on Pascal/CPU is numerically correct |
| Reference LayerNorm for the oracle | A second by-hand norm | `nn.LayerNorm` | The trusted oracle (D-09) |
| GELU | Hand-rolled tanh-approx erf | `F.gelu(x, approximate="tanh")` | Pure pointwise primitive; GPT-2 `gelu_new`; low narrative value (D-09) |
| Cross-entropy / flatten | Custom loss | `F.cross_entropy(logits.view(B*T,V), targets.view(B*T))` | LOCKED — copy `bigram.py:37-38` verbatim (D-05) |
| Optimizer / LR schedule / AMP / clip / checkpoint / data split | Anything | `training/` (reused UNTOUCHED) | Proven Phase-3 harness; the GPT only swaps in via the forward contract (D-07) |
| Param counting | Manual tensor enumeration with dedup logic | `{p.data_ptr(): p.numel() for p in model.parameters()}` then `sum(values())` | Deduping by `data_ptr` counts the tied tensor exactly once (MODEL-05) — see below |

**Key insight:** the from-scratch boundary is deliberately narrow — hand-roll only what tells the portfolio story (attention math, LayerNorm). Everything with a trusted PyTorch primitive (GELU, CE, sdpa-as-oracle, optimizer, autocast) uses the primitive. Re-implementing those adds bug surface without narrative payoff.

## Runtime State Inventory

Not applicable — this is a **greenfield** model file (`gpt.py` is new), not a rename/refactor/migration. No stored data, live-service config, OS-registered state, secrets, or build artifacts carry a string this phase changes.

- **Stored data:** None — no datastore touched.
- **Live service config:** None.
- **OS-registered state:** None.
- **Secrets/env vars:** None.
- **Build artifacts:** None — `gpt.py` is a pure-Python addition under the already-installed `personacore` package; no reinstall needed (editable install picks it up).

## Common Pitfalls

### Pitfall 1: Mask applied at the wrong place (the MODEL-06 target bug)
**What goes wrong:** Causal mask added after softmax, or `tril` comparison inverted (`==1` instead of `==0`), or `masked_fill` using `0.0`/a large finite negative instead of `-inf` — future tokens leak probability into earlier positions.
**Why it happens:** The bug is silent — loss still decreases, the model still trains, generation still produces text. Only a causality-perturbation test catches it.
**How to avoid:** `att.masked_fill(self.tril[:,:,:T,:T] == 0, float("-inf"))` strictly **before** `F.softmax(att, dim=-1)`. The MODEL-06 test (below) is the guard.
**Warning signs:** Overfit loss is suspiciously good; causality-perturbation test fails.

### Pitfall 2: Weight tying that isn't a true shared tensor (MODEL-03)
**What goes wrong:** Copying values (`lm_head.weight.data = wte.weight.data.clone()`) instead of sharing the `nn.Parameter` object → two tensors, `data_ptr()` differ, param count double-counts, gradients don't couple.
**Why it happens:** `.data =` or `copy_` looks like tying but isn't.
**How to avoid:** `self.lm_head.weight = self.wte.weight` (assign the Parameter object). Then `model.lm_head.weight.data_ptr() == model.wte.weight.data_ptr()` is `True`.
**Warning signs:** `data_ptr()` test fails; param count comes out ~3.15M too high (one extra `vocab×n_embd` block).

### Pitfall 3: Residual-scaled init applied to only `c_proj` (MODEL-04 / D-04a)
**What goes wrong:** Scaling `c_proj` but not `fc_out` — the MLP output projection writes to the residual stream too and needs the same `0.02/√(2·n_layer)` scaling.
**Why it happens:** The roadmap success criterion literally says "residual-scaled `c_proj`," singular.
**How to avoid:** Iterate `named_parameters()` and scale **both** suffixes `c_proj.weight` and `fc_out.weight`. The init-std test asserts both.
**Warning signs:** `fc_out.weight.std()` ≈ 0.02 instead of ≈ 0.00577.

### Pitfall 4: Causality/equivalence test polluted by dropout or non-eval mode
**What goes wrong:** Tests run with `dropout > 0` or in `train()` mode → random masking makes "unchanged logits" and "manual == sdpa" non-deterministic and flaky.
**Why it happens:** `ModelConfig.dropout=0.0` by default so it's usually fine, but a test that constructs a config with dropout, or forgets `model.eval()`, breaks.
**How to avoid:** All MODEL-03/04/06 + equivalence tests call `model.eval()` and use `dropout=0.0`; wrap in `torch.no_grad()`; `seed_everything`/`torch.manual_seed` first. (Mirror `tests/test_overfit_batch.py:27` and `tests/test_bigram_model.py:42` seeding.)
**Warning signs:** Test passes/fails intermittently across runs.

### Pitfall 5: Manual-vs-sdpa mismatch from shape/scale convention drift
**What goes wrong:** Manual path forgets the `1/sqrt(d_head)` scale, or reshapes heads inconsistently (`d_head = n_embd // n_head = 384//6 = 64`), or transposes wrong → `allclose` fails.
**Why it happens:** `F.scaled_dot_product_attention` scales by `1/sqrt(E)` where `E` is the last-dim head size internally; the manual path must use the SAME `1/sqrt(d_head)` and the SAME `(B, n_head, T, d_head)` layout.
**How to avoid:** Both paths consume the identical `(B, n_head, T, d_head)` q/k/v; manual uses `/ math.sqrt(d_head)`; test with `atol=1e-5` (fp32 CPU). Feed both paths the same q/k/v (factor the projection out of the branch).
**Warning signs:** `allclose` fails by a constant factor (= `sqrt(d_head)`).

### Pitfall 6: Variance convention mismatch in hand-rolled LayerNorm
**What goes wrong:** Using `unbiased=True` (sample variance, `/(N-1)`) → diverges from `nn.LayerNorm` (population, `/N`).
**How to avoid:** `x.var(dim=-1, keepdim=True, unbiased=False)`, `eps=1e-5`.
**Warning signs:** Oracle `allclose` fails at ~1e-3 (grows as the last dim shrinks).

## Code Examples

### Param counting that counts tied weights once (MODEL-05)
```python
# Dedup by storage pointer so the shared wte/lm_head tensor counts exactly once.
def count_parameters(model) -> int:
    seen = {}
    for p in model.parameters():
        seen[p.data_ptr()] = p.numel()   # same tensor -> same key -> counted once
    return sum(seen.values())

# Test (mirrors the [10e6, 15e6] band, D-11):
def test_param_count_in_target_band():
    model = GPT(ModelConfig())
    n = count_parameters(model)
    assert 10_000_000 <= n <= 15_000_000   # ~13.9M with the locked 6/6/384/256 defaults
```
**Expected arithmetic (D-06 sanity, biases included per D-08):**
- token emb (tied head, counted once): 8192×384 = 3,145,728
- positional emb: 256×384 = 98,304
- per block: q/k/v/c_proj = 4×(384×384 + 384 bias) = 4×147,840 = 591,360; MLP fc_in 384×1536 + 1536 = 591,360, fc_out 1536×384 + 384 = 590,208; 2×LayerNorm = 2×(384+384) = 1,536 → ≈ 1,774,464 per block
- 6 blocks ≈ 10,646,784; ln_f = 768
- **Total ≈ 13,891,584 ≈ 13.9M** — comfortably inside [10M, 15M]. (Planner should let the test assert the band, not the exact number, so a bias-count nuance doesn't break it.)

### Causality-perturbation test (MODEL-06)
```python
# Source: standard causal-attention guard (nanoGPT-style). [ASSUMED]
def test_changing_token_t_cannot_change_earlier_logits():
    torch.manual_seed(1337)
    model = GPT(ModelConfig(block_size=16)); model.eval()   # eval -> dropout off
    B, T, V = 1, 8, model.config.vocab_size
    idx = torch.randint(0, V, (B, T))
    with torch.no_grad():
        logits_a, _ = model(idx)
        idx2 = idx.clone()
        t = 5
        idx2[0, t] = (idx2[0, t] + 1) % V         # perturb token at position t
        logits_b, _ = model(idx2)
    # logits at positions < t must be bit-identical (future cannot influence past)
    assert torch.allclose(logits_a[:, :t, :], logits_b[:, :t, :], atol=1e-6)
    # sanity: position t (and after) DID change, proving the perturbation was real
    assert not torch.allclose(logits_a[:, t, :], logits_b[:, t, :], atol=1e-6)
```
The second assertion is important: without it, a model that ignores its input entirely would "pass" the causality check vacuously.

### Manual-vs-sdpa equivalence (D-01)
```python
def test_manual_attention_matches_sdpa():
    torch.manual_seed(0)
    cfg = ModelConfig(block_size=16)
    m_manual = GPT(cfg, attn_impl="manual").eval()
    m_sdpa = GPT(cfg, attn_impl="sdpa").eval()
    m_sdpa.load_state_dict(m_manual.state_dict())   # SAME weights, only the attn path differs
    idx = torch.randint(0, cfg.vocab_size, (2, 12))
    with torch.no_grad():
        la, _ = m_manual(idx)
        lb, _ = m_sdpa(idx)
    assert torch.allclose(la, lb, atol=1e-5)
```
Sharing weights via `load_state_dict` (rather than two fresh inits) isolates the attention-path difference. Both run on CPU in fp32 (Pascal's flash backend wouldn't engage anyway; PyTorch falls back to the math backend — numerically identical).

### Overfit-single-batch gate (MODEL-02 success criterion #1, D-10)
```python
# Mirror tests/test_overfit_batch.py exactly — only the model changes.
def test_gpt_overfits_single_fixed_batch():
    seed_everything(1337)
    model = GPT(ModelConfig())
    fixed_idx = torch.randint(0, 8192, (4, 16))
    fixed_targets = torch.randint(0, 8192, (4, 16))
    cfg = TrainConfig(lr=1e-3, warmup_steps=0, max_steps=300, batch_size=4)
    final_loss = train(train_config=cfg, model=model,
                       fixed_batch=(fixed_idx, fixed_targets), return_final_loss=True)
    assert float(final_loss) < math.log(8192) - 2.0   # well under the uniform ceiling ~9.0
```
This is the proof the GPT drops into `training/loop.py` with no harness change. (Note: GPT is deeper than the bigram — the executor may need to tune `lr`/`max_steps`; the bigram used `lr=1e-1`, but a 6-layer pre-norm net typically wants a smaller lr like `1e-3` to overfit cleanly. Leave the exact threshold/steps to the executor as Phase 3 did.)

### Autocast-safety (the forward must not fight the fp16 loop)
```python
# The loop wraps forward in runtime.autocast() (loop.py:115). The model must:
#  - NOT call .half()/.float()/.to(dtype) on activations or inputs
#  - NOT hardcode a dtype in masked_fill (float("-inf") is dtype-agnostic — OK)
#  - register the causal buffer as float (autocast handles the matmul dtype)
#  - keep CE in the standard call; F.cross_entropy autocasts to fp32 internally (safe)
# Result: the SAME gpt.py runs under fp32 (default) and fp16 AMP (Phase 5 Kaggle) unchanged.
```

## State of the Art

| Old Approach | Current Approach | When | Impact |
|---|---|---|---|
| Manual softmax-attention everywhere | `F.scaled_dot_product_attention` as a math primitive | PyTorch ≥2.0 | Allowed here as the *oracle*; manual path stays the default for the portfolio narrative (D-01/D-02) |
| Post-LN (original Transformer) | **Pre-LN** (GPT-2/nanoGPT): norm before sublayer, residual around it | GPT-2 era | Locked (MODEL-02). More stable training; `ln_f` after the last block |
| Sinusoidal positional encoding | **Learned** positional embeddings (`wpe`) | GPT-2 | Locked (MODEL-02) |
| Untied output head | **Weight-tied** head (`lm_head.weight = wte.weight`) | GPT-2 | Locked (MODEL-03); saves ~3.15M params, the difference between ~17M and ~13.9M |
| Flat 0.02 init | GPT-2 **residual-scaled** init `0.02/√(2·n_layer)` on residual-output projections | GPT-2 paper | Locked (MODEL-04/D-04a); controls residual-stream variance growth with depth |

**Deprecated/outdated for this phase:** nothing — GPT-2 decoder architecture is stable and unchanged across PyTorch 2.x. The only PyTorch-version-sensitive surface (sdpa backend selection on Pascal) is irrelevant to CPU tests and already documented in CLAUDE.md.

## Validation Architecture

> `nyquist_validation` is not disabled in config → this section is included. This is the spec VALIDATION.md is built from.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest `~=9.0` [VERIFIED: pyproject.toml] |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths=["tests"]`, `pythonpath=["."]`) |
| Quick run command | `pytest tests/test_gpt_model.py -x -q` (or the specific new MODEL test files) |
| Full suite command | `make test` (= `pytest`, CPU-only, GPU-free) |
| Test style precedent | `tests/test_bigram_model.py`, `tests/test_overfit_batch.py` (seed-first, `torch.allclose`, no GPU) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MODEL-02 | GPT (causal MHA mask-before-softmax & 1/√d_head, GELU MLP, pre-norm, learned pos emb, ln_f) overfits one batch through the existing loop | integration (overfit gate) | `pytest tests/test_gpt_overfit.py -x` | ❌ Wave 0 |
| MODEL-02 | Forward returns `(logits (B,T,V), None)` w/o targets and `(logits, scalar_loss)` with targets — contract identical to bigram | unit | `pytest tests/test_gpt_model.py::test_forward_contract -x` | ❌ Wave 0 |
| MODEL-02 | Manual attention path == `F.scaled_dot_product_attention(is_causal=True)` (`allclose atol≈1e-5`) | unit (equivalence) | `pytest tests/test_gpt_attention_equiv.py -x` | ❌ Wave 0 |
| MODEL-02 | Hand-rolled `LayerNorm` == `nn.LayerNorm` (`allclose atol≈1e-6`, population variance) | unit (oracle) | `pytest tests/test_gpt_layernorm.py -x` | ❌ Wave 0 |
| MODEL-03 | `lm_head.weight.data_ptr() == wte.weight.data_ptr()` (true shared tensor) | unit | `pytest tests/test_gpt_weight_tying.py -x` | ❌ Wave 0 |
| MODEL-04 | Per-tensor init std: 0.02 on emb/input-proj; `0.02/√(2·n_layer)` on **c_proj AND fc_out**; biases 0; LN weight 1/bias 0 | unit | `pytest tests/test_gpt_init.py -x` | ❌ Wave 0 |
| MODEL-05 | Param count (tied counted once via `data_ptr` dedup) ∈ `[10e6, 15e6]` | unit | `pytest tests/test_gpt_param_count.py -x` | ❌ Wave 0 |
| MODEL-06 | Perturbing token at `t` leaves logits at `<t` unchanged (`allclose`), AND changes logits at `t` (non-vacuous) | unit | `pytest tests/test_gpt_causality.py -x` | ❌ Wave 0 |
| MODEL-07 | Every adaptable projection is a named `nn.Linear` reachable by name (`q_proj/k_proj/v_proj/c_proj/fc_in/fc_out`), called as a module, no wrapper | unit (structural) | `pytest tests/test_gpt_lora_seam.py -x` | ❌ Wave 0 |

### What could silently pass without each test (sampling rationale)
- **MODEL-06 (causality):** Without it, a mask-after-softmax or inverted-`tril` bug trains and generates normally — the densest silent-bug risk in the whole milestone. This is the single highest-value test. The non-vacuous second assertion (position `t` *did* change) prevents a degenerate "model ignores input" pass.
- **MODEL-04 (init, esp. D-04a):** Without asserting `fc_out` separately, a model that residual-scales only `c_proj` passes — and deep-network training subtly destabilizes with no obvious failure. Sample **both** residual-output suffixes, not just one.
- **MODEL-03 (data_ptr):** A `.clone()`-based "tying" passes any value-equality check but is two tensors; only `data_ptr()` identity catches it. (And it would inflate MODEL-05 by ~3.15M, so the two tests cross-check each other.)
- **Attention equivalence:** Without it, a manual path missing the `1/√d_head` scale or with a head-reshape bug still trains (the network adapts) — equivalence to sdpa is the only proof the hand-rolled math is *correct*, which is the portfolio claim.
- **LayerNorm oracle:** An `unbiased=True` variance bug shifts activations slightly; training still works, so only the oracle catches the convention error.
- **MODEL-02 overfit:** The end-to-end "it plugs into the loop and learns" proof; a shape/contract break that unit tests miss surfaces here.
- **MODEL-07 structural:** Guards the M2 bridge — if a refactor fuses `c_attn` or inlines a projection as `F.linear`, M2 LoRA can't wrap it. Cheap insurance for the milestone's headline feature.

### Sampling Rate
- **Per task commit:** `pytest tests/test_gpt_*.py -x -q` (the new MODEL files only — fast, CPU).
- **Per wave merge:** `make test` (full suite — ensures the GPT swap didn't regress the Phase-1/2/3 harness).
- **Phase gate:** full suite green before `/gsd:verify-work`. The overfit gate is the slowest (~hundreds of steps on CPU); keep its `max_steps`/model size minimal (it uses the real `ModelConfig`, so consider a smaller `block_size`/`n_layer` config in the test if CPU time is a concern — but the success criterion wants the *real* config to overfit, so prefer the real config with a bounded step budget).

### Wave 0 Gaps
- [ ] `tests/test_gpt_model.py` — forward contract (covers MODEL-02 contract)
- [ ] `tests/test_gpt_attention_equiv.py` — manual vs sdpa (MODEL-02)
- [ ] `tests/test_gpt_layernorm.py` — hand-rolled vs `nn.LayerNorm` (MODEL-02)
- [ ] `tests/test_gpt_weight_tying.py` — `data_ptr()` identity (MODEL-03)
- [ ] `tests/test_gpt_init.py` — per-tensor init std incl. `c_proj`+`fc_out` (MODEL-04)
- [ ] `tests/test_gpt_param_count.py` — dedup count in [10M,15M] (MODEL-05)
- [ ] `tests/test_gpt_causality.py` — perturbation guard (MODEL-06)
- [ ] `tests/test_gpt_lora_seam.py` — named-module structural check (MODEL-07)
- [ ] `tests/test_gpt_overfit.py` — overfit-one-batch through `train()` (MODEL-02 SC#1)
- [ ] Framework install: none — pytest already present.
- [ ] Shared fixtures: none new strictly required; a small `gpt_eval_model` fixture (eval-mode GPT with a tiny `block_size`) could DRY the causality/equivalence tests but is optional.

*(No conftest change needed; existing `tests/conftest.py` `simulate_pascal` fixture is unused by these CPU-only model tests.)*

## Security Domain

> `security_enforcement` is not disabled in config, but this is an offline, on-device, from-scratch ML library with no network/auth/IO surface in this phase. ASVS web categories are largely N/A; the relevant controls are supply-chain and deserialization safety.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth surface — local library |
| V3 Session Management | no | No sessions |
| V4 Access Control | no | No access boundaries |
| V5 Input Validation | minimal | Model assumes in-range `idx` (`0..vocab_size-1`); the tokenizer (Phase 2) is the validation boundary. Optionally assert `idx.max() < vocab_size` in tests, not the hot path |
| V6 Cryptography | no | Never hand-roll crypto — none needed here |
| V14 / Supply Chain | yes | **No new dependency added** this phase (PyTorch-only). The from-scratch ethos *is* the supply-chain control — no HF model code, no `flash-attn`, no LoRA package |
| Deserialization safety | future | Not this phase. `safetensors`/`weights_only` checkpoint loading is a Phase-8 concern (DEMO-02); Phase-4 tests construct models in-process, never load untrusted files |

### Known Threat Patterns for from-scratch PyTorch model

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Slopsquatted/typosquatted ML package | Tampering | N/A — zero new packages installed this phase |
| Arbitrary code via `torch.load` pickle | Tampering/Elevation | Out of scope here (no file loads in Phase-4 tests); Phase 8 uses `safetensors`/`weights_only=True` |
| Index out of range (`idx >= vocab_size`) → CUDA/CPU crash | DoS | Tokenizer is the upstream validation boundary (Phase 2); optional in-range assert in tests |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | GPT-2 init: `nn.Linear` & embeddings std=0.02, biases 0, residual-output projections `0.02/√(2·n_layer)`, LayerNorm weight=1/bias=0 | Pattern 2 / MODEL-04 | LOW — this is the canonical GPT-2/nanoGPT recipe and matches D-04/D-04a verbatim; the test itself *asserts* these stds, so a wrong constant fails loudly, not silently |
| A2 | `nn.LayerNorm` uses population variance (`unbiased=False`) + `eps=1e-5` default | Pattern 4 / Pitfall 6 | LOW — long-standing PyTorch behavior; the oracle test would expose any mismatch |
| A3 | `F.scaled_dot_product_attention(is_causal=True)` scales by `1/√(head_dim)` matching the manual `1/√d_head`, and falls back to the math backend on CPU/Pascal (numerically equivalent to manual) | Pattern (attn) / Pitfall 5 | LOW — documented PyTorch ≥2.0 semantics + CLAUDE.md's Pascal-fallback note; the `allclose(atol=1e-5)` equivalence test is the direct check |
| A4 | `F.gelu(approximate="tanh")` matches GPT-2 `gelu_new` | Don't-Hand-Roll | LOW — D-08 specifies tanh-approx; not separately asserted (no oracle), but it's the standard mapping |
| A5 | Overfit may need a smaller `lr` (~1e-3) than the bigram's 1e-1 for a 6-layer net | Overfit example | LOW — the executor tunes the threshold/steps exactly as Phase 3 left them to the executor (A2 precedent) |
| A6 | Total param count ≈ 13.9M with biases included | Code Examples (count) | LOW — the test asserts a *band* [10M,15M], not the exact figure, so bias-count nuances don't break it |

**Note:** Every A* claim above is either (a) asserted by the very test it informs (so a wrong assumption fails the test rather than shipping a bug), or (b) directly locked in CONTEXT.md. None require user confirmation before planning — they're standard GPT-2 facts the test suite verifies empirically. The `[ASSUMED]` tags reflect "from training knowledge, not re-verified against live docs this session," per provenance policy.

## Open Questions

1. **Exact overfit `lr`/`max_steps`/`block_size` for the GPT overfit test on CPU**
   - What we know: bigram used `lr=1e-1, max_steps=300`; a 6-layer pre-norm GPT typically overfits a tiny fixed batch with `lr≈1e-3` over a few hundred steps.
   - What's unclear: precise values that keep CPU runtime acceptable while reliably driving loss < `ln(8192)-2`.
   - Recommendation: leave to the executor (Phase-3 precedent A2); the test asserts a band, not a fixed loss. If the full-`ModelConfig` overfit is too slow on CI, use a reduced-`block_size` config in the test while keeping the *architecture* identical.

2. **Whether the `attn_impl` toggle is a `ModelConfig` field or a `GPT` constructor arg**
   - What we know: D-02 explicitly delegates the *mechanism* to the planner ("a `ModelConfig` field vs a constructor arg") — intent is "manual default, switchable, equivalence-tested."
   - Recommendation: a constructor arg `attn_impl="manual"` keeps `ModelConfig` (which is serialized into every checkpoint via `asdict`) clean of a runtime-only flag, while still letting Phase 5 pass `attn_impl="sdpa"`. Either is acceptable per D-02; flag it for the planner to pick.

## Project Constraints (from CLAUDE.md)

- **From-scratch only:** No HuggingFace `transformers`/`peft` model or adapter code. Core ML built by hand. `nn`/`F` primitives allowed; `F.scaled_dot_product_attention` and `nn.LayerNorm` are allowed as math primitives/oracles (CLAUDE.md "What NOT to Use" + D-01/D-09).
- **No bf16 / no `torch.compile` / no `flash-attn`:** Pascal constraints; irrelevant to CPU tests but the model must not assume any of them.
- **CPU-only tests:** every Phase-4 test runs GPU-free (Phase-1 CI, Python 3.11).
- **Autocast-safe model:** no manual `.half()`/dtype juggling; `RuntimeConfig` is the single device/AMP source of truth (never call `torch.cuda.*` in the model).
- **Reused harness untouched:** `training/`, `config.py`, `checkpoint.py`, `logging.py` unchanged (D-07).
- **No CLI/argparse:** thin `scripts/` entry points only (Phase-1 D-04). Phase 4 likely needs no new script at all (tests cover everything; the loop already runs the model).
- **GSD workflow:** edits go through a GSD command; atomic commits; `make lint` (`ruff check && ruff format --check`) + `make test` gate. Ruff line-length 100, import-sort (`I`) enabled — match existing file style.
- **`vocab_size=8192`, `eos_id=8184` LOCKED** — read from `ModelConfig`, never re-pick (D-06).

## Sources

### Primary (HIGH confidence) — the binding sources for this phase
- `/Users/juliorcoelho/PersonaCore/.planning/phases/04-gpt-transformer-decoder/04-CONTEXT.md` — D-01..D-11 (all locked decisions; the authoritative spec)
- `/Users/juliorcoelho/PersonaCore/src/personacore/model/bigram.py` — locked `forward(idx, targets) -> (logits, loss)` contract + CE flatten (lines 31-39) the GPT copies verbatim
- `/Users/juliorcoelho/PersonaCore/src/personacore/config.py` — `ModelConfig` (8192/8184/256/6/6/384/0.0), `RuntimeConfig.autocast`
- `/Users/juliorcoelho/PersonaCore/src/personacore/training/loop.py` — the untouched harness the GPT plugs into (autocast wrap line 115; `assemble_loss(base, ())` line 117)
- `/Users/juliorcoelho/PersonaCore/src/personacore/training/loss.py` — `assemble_loss` (model-stays-pure boundary, D-05)
- `/Users/juliorcoelho/PersonaCore/tests/test_overfit_batch.py`, `tests/test_bigram_model.py`, `tests/conftest.py` — the test idiom the MODEL gates mirror (seed-first, `allclose`, CPU-only)
- `/Users/juliorcoelho/PersonaCore/.planning/REQUIREMENTS.md` (MODEL-02..07) + `.planning/ROADMAP.md` (Phase 4 goal + 5 success criteria)
- `/Users/juliorcoelho/PersonaCore/CLAUDE.md` — stack discipline, from-scratch boundary, Pascal constraints
- `/Users/juliorcoelho/PersonaCore/pyproject.toml` — pytest `~=9.0`, ruff config, test paths

### Secondary (training-knowledge, standard architecture — tagged `[ASSUMED]`)
- GPT-2 / nanoGPT canonical decoder architecture (pre-norm blocks, learned pos emb, weight tying, `0.02/√(2·n_layer)` residual init, `gelu_new` tanh-approx) — used as the *conceptual* reference, hand-implemented; every numeric claim is re-verified by the phase's own tests.

### Tertiary (LOW confidence)
- None — no claim in this research rests on unverified web search; the architecture is canonical and the codebase contracts are read directly.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages; PyTorch-only, read from pyproject/CLAUDE.md.
- Architecture: HIGH — every decision is pre-locked in CONTEXT.md (D-01..D-11) and the contracts are read from source; GPT-2 architecture is stable across PyTorch 2.x.
- Pitfalls: HIGH — derived from the explicit MODEL-03..06 silent-bug targets and the variance/scale/tying mechanics, each cross-checked against a concrete test design.
- Validation: HIGH — requirement→test map is 1:1 with MODEL-02..07 and mirrors the proven Phase-3 test style.

**Research date:** 2026-06-05
**Valid until:** 2026-09-05 (stable — GPT-2 decoder math and the locked contracts do not move; the only volatile surface, PyTorch sdpa Pascal behavior, is irrelevant to CPU tests)
