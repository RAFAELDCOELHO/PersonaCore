"""Phase 10 — from-scratch EWC core (EWC-01..02): public import surface.

Plan 10-01 ships ``estimate_fisher`` (per-example empirical diagonal Fisher with
mean-normalization and half-split convergence stats, EWC-01 / D-01..D-05); the ``EWCPenalty``
quadratic-penalty callable (EWC-02) extends this surface in the same plan.
"""

from .fisher import estimate_fisher

__all__ = ["estimate_fisher"]
