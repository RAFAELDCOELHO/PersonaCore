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
