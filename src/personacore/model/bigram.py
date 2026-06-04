"""From-scratch bigram baseline language model (MODEL-01 / D-01 / D-02 / D-03).

The bigram is the Phase-3 throwaway that proves the harness (training loop, checkpoint,
sampling) BEFORE the real GPT (Phase 4) exists. Its only parameter is a lookup table —
``nn.Embedding(vocab_size, vocab_size)`` — where row ``i`` IS the next-token logits given
the current token ``i`` (D-01). No attention, no MLP, no positional information: a token's
prediction depends only on itself.

Load-bearing contract:
- D-02: ``forward(idx, targets=None) -> (logits, loss)`` is the LOCKED signature the Phase-4
  transformer will honor UNCHANGED. ``logits.shape == (B, T, vocab_size)``; without targets
  the loss slot is ``None`` (sampling path), with targets it is a scalar cross-entropy.
- D-02a: cross-entropy uses the nanoGPT ``(B*T, V)`` vs ``(B*T)`` flatten so the identical
  call works for the GPT in Phase 4.
- D-03: the model stays PURE — base cross-entropy ONLY. Loss assembly (the M2 EWC seam) lives
  in ``training/loss.py``, never here; no penalties, no ``assemble_loss`` in this file.
- D-11: no ``generate``/``sample`` method — minimal sampling lives in the training loop (Plan 04).
"""

import torch.nn as nn
import torch.nn.functional as F


class BigramLanguageModel(nn.Module):
    """Lookup-table bigram LM: one ``nn.Embedding(vocab_size, vocab_size)`` of next-token logits."""

    def __init__(self, vocab_size: int):
        super().__init__()
        self.token_table = nn.Embedding(vocab_size, vocab_size)

    def forward(self, idx, targets=None):
        logits = self.token_table(idx)  # (B, T, V) — row idx[b, t] is the next-token logits.
        if targets is None:
            return logits, None
        B, T, V = logits.shape
        loss = F.cross_entropy(logits.view(B * T, V), targets.view(B * T))
        return logits, loss
