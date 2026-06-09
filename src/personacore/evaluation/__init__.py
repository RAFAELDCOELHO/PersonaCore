"""Evaluation toolkit — public import surface (EVAL-01).

Re-exports the deterministic full-corpus ``perplexity`` sweep (07-01). A strided /
sliding-window variant is deferred (D-01 locks non-overlapping windows).
"""

from .perplexity import perplexity

__all__ = ["perplexity"]
