"""From-scratch ``LoRALinear`` composition wrapper (LORA-01 / D-05).

Wraps a frozen base ``nn.Linear`` and adds a rank-r delta ``scale * (x @ A^T @ B^T)`` on a
flag-gated branch. Composition, not inheritance: the base module stays byte-identical and its
weights keep their own state-dict slot (the ``.base.`` infix) — which is exactly why injection
must happen AFTER loading base weights.

Identity gate: ``lora_B`` starts at zero, so the wrapper is BIT-identical to the bare Linear at
init (PITFALLS P2). ``scale`` (alpha/r) is computed once in ``__init__`` — the single source of
truth read by forward now and by the Plan-03 merge later (PITFALLS P3). ``enabled``/``merged``
are plain Python bools so they can never leak into ``state_dict()`` or artifacts (D-05).

Autocast-safety rule (inherited verbatim from ``model/gpt.py``): never call ``torch.cuda.*``
and never do manual dtype casting — the training loop's ``RuntimeConfig.autocast()`` owns dtype.
"""

import torch
import torch.nn as nn


class LoRALinear(nn.Module):
    """Composition wrapper: frozen base Linear + trainable rank-r A/B delta (LORA-01)."""

    def __init__(self, base: nn.Linear, r: int, alpha: float, dropout: float = 0.0):
        super().__init__()
        self.base = base  # the frozen original nn.Linear (composition, not inheritance).
        self.scale = alpha / r  # SINGLE source of truth — forward AND merge read this (P3).
        # Fresh explicit-shape tensors, never weight.T views (PITFALLS P5 / MPS contiguity).
        self.lora_A = nn.Parameter(torch.empty(r, base.in_features))
        self.lora_B = nn.Parameter(torch.zeros(base.out_features, r))  # ZEROS — identity gate.
        nn.init.normal_(self.lora_A, mean=0.0, std=0.02)  # A-Gaussian, house init std (LORA-01).
        self.dropout = nn.Dropout(dropout)  # LoRA branch only, applied to x before A.
        # Plain Python bools — NOT parameters/serialized state, so they never enter
        # state_dict() and cannot pollute artifacts (D-05).
        self.enabled = True
        self.merged = False

    def forward(self, x):
        y = self.base(x)
        if self.enabled and not self.merged:  # D-05: the branch never executes when disabled.
            y = y + self.scale * (self.dropout(x) @ self.lora_A.T @ self.lora_B.T)
        return y
