"""From-scratch GPT-2-style transformer decoder (MODEL-02..07 / D-01..D-11).

The central "I built a transformer" deliverable: a ~13.9M-parameter hand-rolled GPT-2 decoder
(``GPT``, ``Block``, ``CausalSelfAttention``, ``MLP``, ``LayerNorm``) that honors the LOCKED
``forward(idx, targets=None) -> (logits, loss)`` contract verbatim from ``bigram.py`` so it drops
into the proven Phase-3 training loop with ZERO harness changes (D-05/D-07).

Purity rule (mirrors ``bigram.py``):
- D-05: the model is a PURE ``(logits, loss)`` producer — base cross-entropy ONLY. No
  ``assemble_loss`` (the M2 EWC seam lives in ``training/loss.py``), no ``generate``/``sample``
  (sampling lives in ``training/loop.py``), and NO import from ``training/``.
- Autocast-safe: never call ``torch.cuda.*`` and never do manual dtype casting
  (``.half()``/``.float()``/``.to(dtype)``). ``RuntimeConfig.autocast()`` (the loop) owns dtype.
  ``float("-inf")`` in ``masked_fill`` is dtype-agnostic (OK); the causal buffer is float.

From-scratch boundary (D-01/D-08/D-09): attention math and LayerNorm are hand-rolled; ``F.gelu``,
``F.cross_entropy``, and ``F.scaled_dot_product_attention`` (the ``sdpa`` toggle / equivalence
oracle) are allowed math primitives. Six named ``nn.Linear`` projections per block
(``q_proj``/``k_proj``/``v_proj``/``c_proj``/``fc_in``/``fc_out``) leave the M2 LoRA seam open
(naming only — no wrapper, D-03/D-04).
"""

import math

import torch
import torch.nn as nn
import torch.nn.functional as F

from ..config import ModelConfig


class LayerNorm(nn.Module):
    """Hand-rolled LayerNorm (D-09).

    POPULATION variance (``unbiased=False``) + ``eps=1e-5`` to match ``nn.LayerNorm``'s defaults
    (RESEARCH Pitfall 6 — an ``unbiased=True`` bug diverges at ~1e-3). ``weight`` init 1, ``bias``
    init 0 (set here, so ``_init_weights`` needs no LayerNorm dispatch).
    """

    def __init__(self, ndim: int, eps: float = 1e-5):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(ndim))
        self.bias = nn.Parameter(torch.zeros(ndim))
        self.eps = eps

    def forward(self, x):
        mean = x.mean(dim=-1, keepdim=True)
        var = x.var(dim=-1, keepdim=True, unbiased=False)  # population variance (== nn.LayerNorm)
        return (x - mean) / torch.sqrt(var + self.eps) * self.weight + self.bias


class CausalSelfAttention(nn.Module):
    """Hand-rolled causal multi-head self-attention — the from-scratch centerpiece (D-01).

    Separate named ``q_proj``/``k_proj``/``v_proj`` input projections (D-03 — NOT a fused
    ``c_attn``) and a ``c_proj`` output projection (the residual-stream writer). The manual path
    masks BEFORE softmax (MODEL-06) and uses the same ``1/sqrt(d_head)`` scale and
    ``(B, n_head, T, d_head)`` layout as ``F.scaled_dot_product_attention`` so the two paths are
    numerically equivalent (Pitfall 5). ``attn_impl`` toggles manual (default) vs sdpa (D-02).
    """

    def __init__(self, config: ModelConfig, attn_impl: str = "manual"):
        super().__init__()
        assert config.n_embd % config.n_head == 0
        self.n_head = config.n_head
        self.n_embd = config.n_embd
        self.attn_impl = attn_impl
        self.d_head = config.n_embd // config.n_head

        # Separate input projections (D-03) + output projection (residual writer); biases ON (D-08).
        self.q_proj = nn.Linear(config.n_embd, config.n_embd)
        self.k_proj = nn.Linear(config.n_embd, config.n_embd)
        self.v_proj = nn.Linear(config.n_embd, config.n_embd)
        self.c_proj = nn.Linear(config.n_embd, config.n_embd)

        self.attn_dropout = nn.Dropout(config.dropout)
        self.resid_dropout = nn.Dropout(config.dropout)

        # Non-persistent causal mask buffer — a derived constant of block_size (Pattern 3).
        self.register_buffer(
            "tril",
            torch.tril(torch.ones(config.block_size, config.block_size)).view(
                1, 1, config.block_size, config.block_size
            ),
            persistent=False,
        )

    def forward(self, x):
        B, T, C = x.shape

        # Project to q/k/v OUTSIDE the branch so both paths consume identical tensors.
        q = self.q_proj(x).view(B, T, self.n_head, self.d_head).transpose(1, 2)
        k = self.k_proj(x).view(B, T, self.n_head, self.d_head).transpose(1, 2)
        v = self.v_proj(x).view(B, T, self.n_head, self.d_head).transpose(1, 2)

        if self.attn_impl == "sdpa":
            y = F.scaled_dot_product_attention(q, k, v, is_causal=True, dropout_p=0.0)
        else:  # "manual" (default) — the from-scratch path.
            att = (q @ k.transpose(-2, -1)) / math.sqrt(self.d_head)
            # Mask BEFORE softmax (MODEL-06): future positions get -inf so they vanish post-softmax.
            att = att.masked_fill(self.tril[:, :, :T, :T] == 0, float("-inf"))
            att = F.softmax(att, dim=-1)
            att = self.attn_dropout(att)
            y = att @ v

        y = y.transpose(1, 2).contiguous().view(B, T, C)  # reassemble heads.
        y = self.resid_dropout(self.c_proj(y))
        return y


class MLP(nn.Module):
    """Position-wise feed-forward MLP — HF-style names ``fc_in``/``fc_out`` (D-04).

    ``fc_out`` is the MLP's residual-stream writer (residual-scaled init, D-04a). GELU is the
    GPT-2 ``gelu_new`` tanh-approx via ``F.gelu`` (a pure primitive — do NOT hand-roll, D-08/D-09).
    """

    def __init__(self, config: ModelConfig):
        super().__init__()
        self.fc_in = nn.Linear(config.n_embd, 4 * config.n_embd)
        self.fc_out = nn.Linear(4 * config.n_embd, config.n_embd)
        self.dropout = nn.Dropout(config.dropout)

    def forward(self, x):
        x = self.fc_in(x)
        x = F.gelu(x, approximate="tanh")
        x = self.fc_out(x)
        x = self.dropout(x)
        return x


class Block(nn.Module):
    """Pre-norm transformer block (D-08/MODEL-02): norm BEFORE the sublayer, residual AROUND it."""

    def __init__(self, config: ModelConfig, attn_impl: str = "manual"):
        super().__init__()
        self.ln_1 = LayerNorm(config.n_embd)
        self.attn = CausalSelfAttention(config, attn_impl)
        self.ln_2 = LayerNorm(config.n_embd)
        self.mlp = MLP(config)

    def forward(self, x):
        x = x + self.attn(self.ln_1(x))  # residual around attention.
        x = x + self.mlp(self.ln_2(x))  # residual around MLP.
        return x


class GPT(nn.Module):
    """Hand-rolled ~13.9M-param GPT-2 decoder honoring the LOCKED forward contract (D-05/D-06).

    ``attn_impl`` is a CONSTRUCTOR arg (not a ModelConfig field, RESEARCH Open Q2) so the
    serialized config stays free of a runtime-only flag; defaults to "manual" (D-02). Pure model:
    base CE only — no assemble_loss/generate/torch.cuda (D-05).
    """

    def __init__(self, config: ModelConfig, attn_impl: str = "manual"):
        super().__init__()
        self.config = config
        self.wte = nn.Embedding(config.vocab_size, config.n_embd)  # token embedding (tied head).
        # Learned positional embedding — gated by use_pos_emb (EVAL-03). Under the no-pos ablation
        # wpe is not registered at all, so its block_size*n_embd params drop from the count
        # (the test_no_pos -98,304 delta requires wpe to be absent from model.parameters()).
        if config.use_pos_emb:
            self.wpe = nn.Embedding(config.block_size, config.n_embd)
        self.drop = nn.Dropout(config.dropout)
        self.blocks = nn.ModuleList([Block(config, attn_impl) for _ in range(config.n_layer)])
        self.ln_f = LayerNorm(config.n_embd)
        # Bias-free head: the tied weight is the ONLY head parameter (a head bias would be untied).
        self.lm_head = nn.Linear(config.n_embd, config.vocab_size, bias=False)

        # Ordering is load-bearing (Pattern 1): base init -> residual-scaled override -> tie.
        # (1) GPT-2 base init over ALL params.
        self.apply(self._init_weights)
        # (2) Residual-scaled override on BOTH residual-stream writers (D-04a — c_proj AND fc_out).
        for name, p in self.named_parameters():
            if name.endswith("c_proj.weight") or name.endswith("fc_out.weight"):
                torch.nn.init.normal_(p, mean=0.0, std=0.02 / math.sqrt(2 * config.n_layer))
        # (3) Weight tying AFTER init: gated by weight_tying (EVAL-03). When tied, share the SAME
        # nn.Parameter so data_ptr() is identical (NOT a .data.clone()/copy_, which makes two
        # tensors — RESEARCH Pitfall 2). The surviving tensor is the embedding init (std 0.02);
        # lm_head is never separately re-initialized. Under the untie ablation, lm_head keeps its
        # own freshly-init'd tensor (distinct data_ptr, +vocab_size*n_embd params).
        if config.weight_tying:
            self.lm_head.weight = self.wte.weight

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
        # Hand-rolled LayerNorm weight=1/bias=0 are set in its own __init__ — no dispatch needed.

    def forward(self, idx, targets=None):
        B, T = idx.shape
        assert T <= self.config.block_size, f"seq len {T} > block_size {self.config.block_size}"
        tok_emb = self.wte(idx)  # (B, T, C)
        x = tok_emb
        if self.config.use_pos_emb:
            pos = torch.arange(T, device=idx.device)
            x = x + self.wpe(pos)  # (T, C) — broadcasts over batch.
        x = self.drop(x)
        for block in self.blocks:
            x = block(x)
        x = self.ln_f(x)
        logits = self.lm_head(x)  # (B, T, V)
        # LOCKED bigram tail (D-05) — identical flatten to bigram.py:35-39.
        if targets is None:
            return logits, None
        B, T, V = logits.shape
        loss = F.cross_entropy(logits.view(B * T, V), targets.view(B * T))
        return logits, loss
