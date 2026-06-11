# Phase 4: GPT Transformer Decoder - Pattern Map

**Mapped:** 2026-06-05
**Files analyzed:** 11 (1 new source, 1 modified export, 9 new test files)
**Analogs found:** 11 / 11 (every new file has a strong in-repo analog)

> **Headline for the planner:** This phase is *additive only*. The single new source file
> `src/personacore/model/gpt.py` plugs into the **already-proven Phase-3 harness via the locked
> `forward(idx, targets=None) -> (logits, loss)` contract**. `training/loop.py`, `config.py`,
> `checkpoint.py`, `loss.py`, `seeding.py` are **REUSED UNTOUCHED** — zero harness changes. The
> nine test files mirror the existing seed-first / `torch.allclose` / CPU-only idiom verbatim.

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/personacore/model/gpt.py` | model | request-response (`(idx,targets)->(logits,loss)`) | `src/personacore/model/bigram.py` | exact (same contract, same CE flatten, same purity rule) |
| `src/personacore/model/__init__.py` (modified) | config/export | n/a (barrel export) | itself (line 7-9, mirror `BigramLanguageModel` export) | exact |
| `tests/test_gpt_model.py` | test | request-response (forward contract) | `tests/test_bigram_model.py` | exact |
| `tests/test_gpt_attention_equiv.py` | test | transform (manual vs sdpa equivalence) | `tests/test_bigram_model.py` (allclose) + `tests/test_tokenizer_oracle.py` (oracle idiom) | role-match |
| `tests/test_gpt_layernorm.py` | test | transform (hand-rolled vs `nn.LayerNorm` oracle) | `tests/test_tokenizer_oracle.py` (oracle-vs-reference idiom) | role-match |
| `tests/test_gpt_weight_tying.py` | test | structural (`data_ptr()` identity) | `tests/test_bigram_model.py` (construct-and-assert) | role-match |
| `tests/test_gpt_init.py` | test | structural (per-tensor init std) | `tests/test_bigram_model.py` (seeded construct-and-assert) | role-match |
| `tests/test_gpt_param_count.py` | test | structural (data_ptr-dedup count) | `tests/test_bigram_model.py` | role-match |
| `tests/test_gpt_causality.py` | test | transform (perturbation guard, allclose) | `tests/test_bigram_model.py` (allclose + seed) | role-match |
| `tests/test_gpt_lora_seam.py` | test | structural (named-module reachability) | `tests/test_bigram_model.py` (construct-and-assert) | role-match |
| `tests/test_gpt_overfit.py` | test (integration) | event-driven (drive loss->~0 through `train()`) | `tests/test_overfit_batch.py` | exact (reuse the exact harness scaffold) |

---

## Pattern Assignments

### `src/personacore/model/gpt.py` (model, request-response) — THE deliverable

**Analog:** `src/personacore/model/bigram.py`

This is the single new source file. It REPLICATES the bigram's locked contract and CE flatten
exactly, only swapping the body (lookup table → full transformer). The model stays **pure**:
base cross-entropy only, no `assemble_loss`, no `generate`/`sample`, no `torch.cuda.*`, no manual
`.half()`/dtype casting.

**LOCKED forward + CE-flatten pattern to replicate verbatim** (`bigram.py:31-39`):
```python
def forward(self, idx, targets=None):
    logits = self.token_embedding_table(idx)  # (B, T, V)
    if targets is None:
        return logits, None
    B, T, V = logits.shape
    loss = F.cross_entropy(logits.view(B * T, V), targets.view(B * T))
    return logits, loss
```
The GPT's `forward` keeps the SAME structure: build `logits (B,T,V)`; `if targets is None: return
logits, None`; else `F.cross_entropy(logits.view(B*T, V), targets.view(B*T))`. **Do not change the
signature, the `None` slot, or the flatten** — `training/loop.py` calls `_, base_loss = model(xb,
yb)` (loop.py:116) and assumes exactly this. (D-05/D-05a.)

**Purity rule to copy from the bigram's module docstring** (`bigram.py:9-17`):
- D-03/D-05: model is a pure `(logits, loss)` producer; base CE only. Loss assembly (the M2 EWC
  seam) lives in `training/loss.py::assemble_loss`, **never in the model**.
- D-11/D-05: **no** `generate`/`sample` method — sampling already lives in `training/loop.py::sample`
  (loop.py:84-98). Do not add it to the GPT.

**`ModelConfig` fields the constructor reads** (`config.py:64-80`) — the GPT reads sizing from here,
**no new config layer** (D-06):
```python
@dataclass
class ModelConfig:
    vocab_size: int = 8192   # LOCKED by Phase 2 — wte rows AND tied lm_head out-features
    eos_id: int = 8184       # not used by the model body; travels in checkpoint
    block_size: int = 256    # causal-buffer size AND wpe rows; slice [:T,:T]/[:T] per forward
    n_layer: int = 6         # number of Blocks AND the residual-init scale 0.02/sqrt(2*n_layer)
    n_head: int = 6          # heads; d_head = n_embd // n_head = 384//6 = 64
    n_embd: int = 384        # model width; all six projections are nn.Linear(n_embd, ...)
    dropout: float = 0.0     # wired-but-0; applied at attn/residual/MLP points (D-08)
```
Constructor signature: `GPT(config: ModelConfig, attn_impl: str = "manual")` — RESEARCH Open Q2
recommends `attn_impl` as a **constructor arg** (keeps `ModelConfig`, which `save_checkpoint`
`asdict`s into every checkpoint, free of a runtime-only flag). Default `"manual"` (D-02).

**Autocast-safety (from the loop's contract, loop.py:115-117):** the loop wraps forward in
`runtime.autocast()`. The model must NOT call `.half()/.float()/.to(dtype)` on activations, must NOT
call `torch.cuda.*`, and `float("-inf")` in `masked_fill` is dtype-agnostic (OK). `RuntimeConfig`
(`config.py:55-61`) is the single device/AMP source of truth.

**Architecture body** (hand-rolled, per RESEARCH Patterns 1-4 — not re-derived here; see
`04-RESEARCH.md` lines 120-210 for the exact `__init__` order, `_init_weights`, causal buffer, and
hand-rolled LayerNorm code). Six named `nn.Linear` projections per block
(`q_proj/k_proj/v_proj/c_proj/fc_in/fc_out`, D-03/D-04); weight tying via
`self.lm_head.weight = self.wte.weight` set **after** the init pass (RESEARCH Pattern 1).

---

### `src/personacore/model/__init__.py` (export, modified)

**Analog:** itself — the file already documents the exact change in its docstring.

**Current state** (`model/__init__.py:7-9`):
```python
from .bigram import BigramLanguageModel

__all__ = ["BigramLanguageModel"]
```
The module docstring (line 3-4) already pre-specifies the Phase-4 edit: *"Phase 4 adds
`from .gpt import GPT` here unchanged."* Add `from .gpt import GPT` and append `"GPT"` to `__all__`.
This is the ONLY edit to an existing file in the phase.

---

### `tests/test_gpt_model.py` (test — forward contract, MODEL-02)

**Analog:** `tests/test_bigram_model.py` (exact)

**Scaffold to copy** (`test_bigram_model.py:12-36`): module imports `math`, `torch`, the model;
no fixture; random `idx` via `torch.randint`. Three-test shape:
```python
def test_forward_returns_logits_none_without_targets():
    model = BigramLanguageModel(vocab_size=32)
    idx = torch.randint(0, 32, (2, 5))
    logits, loss = model(idx)
    assert logits.shape == (2, 5, 32)
    assert loss is None

def test_forward_returns_scalar_loss_with_targets():
    ...
    logits, loss = model(idx, targets)
    assert isinstance(loss, torch.Tensor)
    assert loss.ndim == 0  # scalar CE over flattened B*T
```
GPT adaptation: construct `GPT(ModelConfig(block_size=16))` (small T), assert `logits.shape ==
(B, T, vocab_size)` and the `None`/scalar-loss slots. Add the random-init loss-near-`ln(vocab)`
sanity (`test_bigram_model.py:39-50`) — but note GPT's tied/scaled init puts it near `ln(8192)`
only loosely; assert a generous band or skip per RESEARCH A6.

---

### `tests/test_gpt_attention_equiv.py` (test — manual vs sdpa, MODEL-02)

**Analog:** `tests/test_bigram_model.py` (seed + `torch.allclose`) + `tests/test_tokenizer_oracle.py`
(reference-oracle idiom, lines 107-109 `assert ours == enc.encode_ordinary(s)`)

**Pattern:** seed first (`torch.manual_seed(0)`), build two GPTs sharing weights via
`load_state_dict`, run both in `eval()` + `no_grad()`, assert `allclose(atol=1e-5)`. Exact test in
RESEARCH lines 326-339:
```python
def test_manual_attention_matches_sdpa():
    torch.manual_seed(0)
    cfg = ModelConfig(block_size=16)
    m_manual = GPT(cfg, attn_impl="manual").eval()
    m_sdpa = GPT(cfg, attn_impl="sdpa").eval()
    m_sdpa.load_state_dict(m_manual.state_dict())  # SAME weights, only attn path differs
    idx = torch.randint(0, cfg.vocab_size, (2, 12))
    with torch.no_grad():
        la, _ = m_manual(idx)
        lb, _ = m_sdpa(idx)
    assert torch.allclose(la, lb, atol=1e-5)
```
`eval()` + `dropout=0.0` are mandatory (RESEARCH Pitfall 4) or the comparison flakes.

---

### `tests/test_gpt_layernorm.py` (test — hand-rolled vs `nn.LayerNorm` oracle, MODEL-02)

**Analog:** `tests/test_tokenizer_oracle.py` (the established "hand-rolled-vs-trusted-reference"
oracle idiom)

**Pattern:** instantiate the hand-rolled `LayerNorm(C)` and `nn.LayerNorm(C)`, feed identical
random fp32 `x` of shape `(B,T,C)`, assert `torch.allclose(custom(x), nn.LayerNorm(C)(x),
atol=1e-6)`. **Load-bearing subtlety** (RESEARCH Pattern 4 / Pitfall 6): hand-rolled must use
`x.var(dim=-1, keepdim=True, unbiased=False)` (population variance) and `eps=1e-5` to match
`nn.LayerNorm`'s defaults — fresh weight=1/bias=0 means no param copy needed. This mirrors the
tokenizer oracle's "prove our math == the trusted primitive" shape.

---

### `tests/test_gpt_weight_tying.py` (test — `data_ptr()` identity, MODEL-03)

**Analog:** `tests/test_bigram_model.py` (construct-and-assert, no fixture)

**Pattern:** `model = GPT(ModelConfig())`, then:
```python
assert model.lm_head.weight.data_ptr() == model.wte.weight.data_ptr()  # SAME tensor, not a copy
```
RESEARCH Pitfall 2 is the target bug: a `.clone()`-based "tying" passes value equality but is two
tensors. Only `data_ptr()` identity catches it. This test cross-checks MODEL-05 (a copy inflates
param count by ~3.15M).

---

### `tests/test_gpt_init.py` (test — per-tensor init std incl. c_proj AND fc_out, MODEL-04)

**Analog:** `tests/test_bigram_model.py:42` (seed-first construct-and-assert)

**Pattern:** `torch.manual_seed(...)` then iterate `model.named_parameters()` asserting the
per-tensor std table (RESEARCH lines 162-173):
| suffix | target std |
|---|---|
| `wte.weight`, `wpe.weight`, `q/k/v_proj.weight`, `fc_in.weight` | ≈ 0.02 |
| **`c_proj.weight` AND `fc_out.weight`** | **≈ 0.02/√(2·6) ≈ 0.005774** |
| all `*.bias`, LayerNorm bias | 0.0 exact |
| LayerNorm weight | all == 1 |

**D-04a is the single most error-prone fact:** the residual-scaled std applies to **BOTH** output
projections (`c_proj` AND `fc_out`), not just `c_proj`. A test that only checks `c_proj` silently
passes a model that mis-inits `fc_out` (RESEARCH Pitfall 3). Assert both suffixes explicitly. Use a
loose tolerance (std of a finite tensor is noisy) — e.g. `abs(p.std() - target) < target*0.1`.

---

### `tests/test_gpt_param_count.py` (test — data_ptr-dedup count, MODEL-05)

**Analog:** `tests/test_bigram_model.py` (construct-and-assert)

**Pattern** (RESEARCH lines 283-296): dedup by storage pointer so the tied tensor counts once:
```python
def count_parameters(model) -> int:
    seen = {}
    for p in model.parameters():
        seen[p.data_ptr()] = p.numel()   # same tensor -> same key -> counted once
    return sum(seen.values())

def test_param_count_in_target_band():
    n = count_parameters(GPT(ModelConfig()))
    assert 10_000_000 <= n <= 15_000_000   # ~13.9M with locked 6/6/384/256 defaults
```
Assert the **band**, not the exact number (D-11 / RESEARCH A6) so a bias-count nuance does not break
it. `register_buffer(..., persistent=False)` keeps the causal mask out of `parameters()` already.

---

### `tests/test_gpt_causality.py` (test — perturbation guard, MODEL-06) — highest-value test

**Analog:** `tests/test_bigram_model.py` (seed + `torch.allclose`)

**Pattern** (RESEARCH lines 307-323): perturb token at position `t`, assert logits at `< t` are
bit-identical AND logits at `t` DID change (non-vacuous):
```python
def test_changing_token_t_cannot_change_earlier_logits():
    torch.manual_seed(1337)
    model = GPT(ModelConfig(block_size=16)); model.eval()
    B, T, V = 1, 8, model.config.vocab_size
    idx = torch.randint(0, V, (B, T))
    with torch.no_grad():
        logits_a, _ = model(idx)
        idx2 = idx.clone(); t = 5
        idx2[0, t] = (idx2[0, t] + 1) % V
        logits_b, _ = model(idx2)
    assert torch.allclose(logits_a[:, :t, :], logits_b[:, :t, :], atol=1e-6)   # past unchanged
    assert not torch.allclose(logits_a[:, t, :], logits_b[:, t, :], atol=1e-6)  # t DID change
```
The second assertion prevents an "ignores its input" model passing vacuously (RESEARCH line 323).
This is the densest silent-bug guard in the milestone (mask-before-softmax). `eval()` + `no_grad()`
mandatory.

---

### `tests/test_gpt_lora_seam.py` (test — named-module structural check, MODEL-07)

**Analog:** `tests/test_bigram_model.py` (construct-and-assert) + `test_tokenizer_oracle.py:112-116`
(structural source scan as a precedent for "assert a structural property")

**Pattern:** construct `GPT(ModelConfig())`, walk `named_modules()`, and assert every block exposes
all six projections as `nn.Linear` reachable by name:
```python
import torch.nn as nn
model = GPT(ModelConfig())
names = {n for n, m in model.named_modules() if isinstance(m, nn.Linear)}
for blk in range(model.config.n_layer):
    for proj in ("q_proj", "k_proj", "v_proj", "c_proj", "fc_in", "fc_out"):
        assert any(n.endswith(f"{blk}.{proj}") or n.endswith(proj) for n in names)
```
Guards the M2 LoRA bridge: if a refactor fuses `c_attn` or inlines a projection as `F.linear`, M2
can't wrap it (RESEARCH line 411). No wrapper / no rank params this phase (D-03/D-04, MODEL-07).

---

### `tests/test_gpt_overfit.py` (test — overfit one batch through `train()`, MODEL-02 SC#1)

**Analog:** `tests/test_overfit_batch.py` (exact — reuse the scaffold, swap only the model)

**Scaffold to copy verbatim** (`test_overfit_batch.py:25-43`):
```python
def test_overfits_single_fixed_batch():
    seed_everything(1337)                                  # determinism FIRST (Pitfall 5)
    model = BigramLanguageModel(vocab_size=8192)           # <-- swap to GPT(ModelConfig())
    fixed_idx = torch.randint(0, 8192, (4, 16))
    fixed_targets = torch.randint(0, 8192, (4, 16))
    cfg = TrainConfig(lr=1e-1, warmup_steps=0, max_steps=300, batch_size=4, grad_accum_steps=1)
    final_loss = train(
        train_config=cfg, model=model,
        fixed_batch=(fixed_idx, fixed_targets), return_final_loss=True,
    )
    assert float(final_loss) < UNIFORM_BOUND - 2.0         # UNIFORM_BOUND = math.log(8192) ~9.0
```
**Only the model changes** — `train()` (loop.py), `TrainConfig` (config.py), `seed_everything`
(seeding.py) are reused UNTOUCHED. This is the proof the GPT drops into the loop with no harness
change. The executor tunes `lr`/`max_steps` for a 6-layer net (RESEARCH suggests `lr≈1e-3` vs the
bigram's `1e-1`; Open Q1) and may use a reduced `block_size` config if CPU time is tight, keeping the
architecture identical. Imports to copy (`test_overfit_batch.py:12-22`):
`from personacore.config import TrainConfig`, `from personacore.seeding import seed_everything`,
`from personacore.training.loop import train`.

---

## Shared Patterns

### The Locked Forward Contract (applies to `gpt.py`)
**Source:** `src/personacore/model/bigram.py:31-39`
**Apply to:** `gpt.py` — replicate the signature, the `None` loss slot, and the
`logits.view(B*T,V)` / `targets.view(B*T)` CE flatten UNCHANGED. The loop calls it at
`loop.py:116` and assumes exactly this shape.
```python
if targets is None:
    return logits, None
B, T, V = logits.shape
loss = F.cross_entropy(logits.view(B * T, V), targets.view(B * T))
return logits, loss
```

### Model Purity (the EWC/loss-assembly seam stays in training/)
**Source:** `src/personacore/training/loss.py:17-28` + `bigram.py:9-17` docstring
**Apply to:** `gpt.py` — the model returns BASE CE only; `assemble_loss(base, ())` (loop.py:117) is
the identity in M1 and the additive EWC seam in M2. Never put loss assembly, penalties, sampling, or
`generate` in the model.

### Test Idiom: seed-first, CPU-only, `torch.allclose`, no fixture
**Source:** `tests/test_bigram_model.py` + `tests/test_overfit_batch.py`
**Apply to:** ALL nine new test files. Conventions:
- Seed at the top of each non-trivial test: `torch.manual_seed(1337)` (unit) or
  `seed_everything(1337)` (`seeding.py:24`, integration/overfit).
- CPU-only, GPU-free — no `.cuda()`, no device juggling (Phase-1 CI runs on Python 3.11 CPU).
- `model.eval()` + `torch.no_grad()` for any determinism-sensitive assert (equivalence, causality,
  layernorm, init) — dropout/train-mode flakes them (RESEARCH Pitfall 4).
- `torch.allclose(..., atol=1e-5)` for fp32-CPU numeric equivalence; `atol=1e-6` for exact-identity
  (causality past-positions, layernorm oracle).
- No new fixture required. `tests/conftest.py`'s `simulate_pascal` fixture is for the bf16-guard
  test only and is unused by these CPU model tests (RESEARCH line 431).

### Reference-Oracle Idiom (hand-rolled math proven against a trusted primitive)
**Source:** `tests/test_tokenizer_oracle.py:83-109`
**Apply to:** `test_gpt_attention_equiv.py` (manual vs `F.scaled_dot_product_attention`) and
`test_gpt_layernorm.py` (hand-rolled vs `nn.LayerNorm`). Same shape as the tokenizer's
"our-algorithm == tiktoken" proof: feed identical input to both, assert equality. The from-scratch
path is the **default/deliverable**; the primitive is the **oracle**, not a replacement.

---

## No Analog Found

None. Every Phase-4 file maps to an existing in-repo analog — the bigram is a deliberate contract
twin for the GPT, and the Phase-3 test suite established the exact test idioms the nine MODEL gates
reuse. No file needs to fall back to RESEARCH.md-only patterns.

---

## REUSED UNTOUCHED (planner: do NOT modify these)

| File | Why it is touched zero | Verified anchor |
|------|------------------------|-----------------|
| `src/personacore/training/loop.py` | GPT plugs in via `model=...`; calls `_, base_loss = model(xb,yb)` and `assemble_loss(base,())` | loop.py:116-117; `train(..., model=, fixed_batch=, return_final_loss=)` signature 129-145 |
| `src/personacore/config.py` | GPT reads sizing from existing `ModelConfig`; no new fields (D-06) | config.py:64-80 |
| `src/personacore/checkpoint.py` | open-dict + `asdict(model_config)` already carries GPT config; tied-weight & non-persistent buffer need no format change | (unchanged) |
| `src/personacore/training/loss.py` | `assemble_loss` is the M2 EWC seam; identity in M1 | loss.py:17-28 |
| `src/personacore/seeding.py` | `seed_everything` reused by the overfit + determinism tests | seeding.py:24-44 |
| `src/personacore/training/{data,schedule}.py` | overfit gate uses `fixed_batch` path; no data/schedule change | loop.py:205-211 |

---

## Metadata

**Analog search scope:** `src/personacore/`, `src/personacore/model/`, `src/personacore/training/`,
`tests/`
**Files scanned:** 6 read in full (`bigram.py`, `model/__init__.py`, `config.py`,
`test_bigram_model.py`, `test_overfit_batch.py`, `conftest.py`, `training/loop.py`,
`training/loss.py`, `seeding.py`, `test_tokenizer_oracle.py`)
**Pattern extraction date:** 2026-06-05
