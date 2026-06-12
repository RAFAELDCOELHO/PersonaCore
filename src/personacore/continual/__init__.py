"""Phase 10 — from-scratch EWC core (EWC-01..02): public import surface.

Plan 10-01 ships ``estimate_fisher`` (per-example empirical diagonal Fisher with
mean-normalization and half-split convergence stats, EWC-01 / D-01..D-05) and ``EWCPenalty``
(the Kirkpatrick quadratic anchor ``(lam/2) * sum(F * (theta - theta_star)**2)``, EWC-02 —
exactly 0.0 at the anchor, fed into the training loop via the ``assemble_loss`` seam).
"""

from .ewc import EWCPenalty
from .fisher import estimate_fisher

__all__ = ["EWCPenalty", "estimate_fisher"]
