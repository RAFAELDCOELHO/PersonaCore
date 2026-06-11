"""From-scratch ``LoRALinear`` composition wrapper (LORA-01 / D-05).

Wraps a frozen base ``nn.Linear`` and adds a rank-r delta ``scale * (x @ A^T @ B^T)`` on a
flag-gated branch. Composition, not inheritance: the base module stays byte-identical and its
weights keep their own state-dict slot (the ``.base.`` infix) — which is exactly why injection
must happen AFTER loading base weights.

Identity gate: ``lora_B`` starts at zero, so the wrapper is BIT-identical to the bare Linear at
init (PITFALLS P2). ``scale`` (alpha/r) is computed once in ``__init__`` — the single source of
truth read by both forward and ``merge()`` (PITFALLS P3). ``enabled``/``merged`` are plain
Python bools so they can never leak into ``state_dict()`` or artifacts (D-05).

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

    @torch.no_grad()
    def merge(self):
        """Fold the adapter delta into ``base.weight`` in place (LORA-04 / D-08 in-place form).

        Stores a lazy clone of the pristine base weight in ``self._w0`` — a plain attribute,
        never registered, so it can never enter ``state_dict()`` or an artifact. The delta
        reads ``self.scale``, the single source of truth set in ``__init__`` (PITFALLS P3:
        never recompute alpha/r here). Shape sanity: ``(out, r) @ (r, in) == (out, in)``.
        """
        assert not self.merged, "double merge would fold the delta twice"
        self._w0 = self.base.weight.detach().clone()  # plain attr — never in state_dict.
        self.base.weight.data.add_(self.scale * (self.lora_B @ self.lora_A))
        self.merged = True

    @torch.no_grad()
    def unmerge(self):
        """Bit-exact restore of the pre-merge base weight (D-07).

        Stored-copy restore == exact round-trip: ``copy_`` from the clone is bit-identical,
        where a float subtraction of the delta would NOT round-trip (fp non-associativity).
        """
        assert self.merged, "unmerge on a never-merged module"
        self.base.weight.data.copy_(self._w0)  # stored-copy restore — bit-exact (D-07).
        self.merged = False
        del self._w0
