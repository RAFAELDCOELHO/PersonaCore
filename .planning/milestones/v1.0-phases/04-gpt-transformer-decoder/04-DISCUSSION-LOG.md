# Phase 4: GPT Transformer Decoder - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-05
**Phase:** 4-gpt-transformer-decoder
**Areas discussed:** Attention math depth, LoRA seam shape

---

## Gray-area selection

| Area | Description | Selected |
|------|-------------|----------|
| Attention math depth | Hand-rolled vs sdpa vs both-with-equivalence | ✓ |
| From-scratch boundary | Hand-roll LayerNorm/GELU vs use nn primitives | (Claude's discretion) |
| GPT-2 vs nanoGPT-lean | Biases / GELU variant / dropout conventions | (Claude's discretion) |
| LoRA seam shape | Fused c_attn vs separate q/k/v; MLP naming | ✓ |

---

## Attention math depth

### Q1 — How should causal self-attention be implemented?

| Option | Description | Selected |
|--------|-------------|----------|
| Both + equiv test | Hand-rolled manual attention AND sdpa path, unit-tested for numerical equivalence; manual is the narrated default | ✓ |
| Hand-rolled only | Explicit manual math only, no sdpa path | |
| sdpa only | `F.scaled_dot_product_attention(is_causal=True)` as the single path | |

**User's choice:** Both + equivalence test.
**Notes:** Manual path computes `(q @ kᵀ)/√d_head`, applies the causal mask **before** softmax,
then `att @ v`. Test asserts `allclose(manual, sdpa, atol≈1e-5)`. Strongest portfolio narrative —
shows the math AND proves it matches the reference primitive.

### Q2 — Which path runs by default, and is it switchable?

| Option | Description | Selected |
|--------|-------------|----------|
| Config toggle, sdpa default | `attn_impl` flag defaulting to sdpa for the Phase-5 run | |
| Config toggle, manual default | `attn_impl` flag, manual math default everywhere; sdpa opt-in | ✓ |
| Manual only at default, sdpa in test | No runtime toggle; sdpa lives only in the equivalence test | |

**User's choice:** Config toggle, manual default.
**Notes:** Default behavior IS the hand-rolled transformer (portfolio-purest). Toggle lets Phase 5
flip to sdpa for memory if needed, without a code change. On P100 the speed gap is modest
(FlashAttention doesn't engage on Pascal — math-backend fallback); the win is memory.

---

## LoRA seam shape

### Q1 — How should the attention QKV projection be structured?

| Option | Description | Selected |
|--------|-------------|----------|
| Fused c_attn | One `nn.Linear(n_embd, 3*n_embd)` split into q,k,v; one module to LoRA-wrap | |
| Separate q/k/v | Three named `q_proj/k_proj/v_proj` + `c_proj`; finer M2 LoRA control | ✓ |

**User's choice:** Separate q/k/v.
**Notes:** Enables the canonical "adapt Q and V, freeze K" LoRA recipe as a per-module choice.
More modules / three small matmuls, acceptable at 10–15M scale. Closer to HF attention naming.

### Q2 — How should the MLP projections be named/scoped for the seam?

| Option | Description | Selected |
|--------|-------------|----------|
| Name all, HF-style | `fc_in`/`fc_out` MLP projections named; all 6 per-block projections LoRA-targetable | ✓ |
| Name all, GPT-2-style | Same coverage but MLP uses `c_fc`/`c_proj` (two `c_proj` names) | |
| Attention-only seam | MLP named mechanically, but M2 targets attention-only | |

**User's choice:** Name all, HF-style.
**Notes:** All six per-block projections — `q_proj`, `k_proj`, `v_proj`, `c_proj`, `fc_in`,
`fc_out` — are named `nn.Linear` modules; M2 can wrap any subset. Flagged init interaction:
GPT-2 residual-scaled init applies to **both** residual-output projections (`c_proj` AND
`fc_out`), not just one — the MODEL-04 init-std check must assert both.

---

## Claude's Discretion

User explicitly delegated the remaining areas and accepted the stated leanings (vetoable in
CONTEXT review):

- **GPT-2-faithful conventions (D-08):** biases ON; GELU tanh-approximation (`gelu_new`); dropout
  wired-but-0.
- **From-scratch boundary (D-09):** hand-roll LayerNorm (with `nn.LayerNorm` equivalence oracle);
  GELU may use the `F`/`nn` primitive.
- **Param sizing (D-06):** keep `ModelConfig` defaults (6L / 6H / 384d / 256 ctx) — already
  ~13.9M params, in target.
- **Overfit gate (D-10)** and **count-tied-once param test (D-11):** reuse Phase-3 patterns.

## Deferred Ideas

- LoRA wrapper math + freezing + rank params — Milestone 2.
- EWC Fisher-penalty computation — Milestone 2 (via the wired `assemble_loss` seam).
- Full-corpus memmap + TinyStories pretraining run — Phase 5.
- Full `generate()` (top-k/top-p, EOS stop) + tests — Phase 6.
- Architecture / LR ablation table — Phase 7.
- Hand-rolling GELU — deferred as low narrative value.
