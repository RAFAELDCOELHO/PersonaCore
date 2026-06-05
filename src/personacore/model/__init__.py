"""From-scratch model package (D-09) — public import surface.

Phase 3 ships the disposable bigram baseline; Phase 4 adds ``from .gpt import GPT`` here
unchanged, honoring the same LOCKED ``forward(idx, targets=None) -> (logits, loss)`` contract.
"""

from .bigram import BigramLanguageModel
from .gpt import GPT

__all__ = ["BigramLanguageModel", "GPT"]
