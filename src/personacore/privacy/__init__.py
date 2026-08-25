"""Phase 22 — DP-SGD core and the (eps, delta) accountant (DPSGD-01/DPSGD-03): package marker.

The FIRST v4.0 content inside ``src/`` (D-10), and that placement is a decision rather than an
accident: a hand-written numerical accountant earns the same portfolio visibility
``evaluation/perplexity.py`` already has, not orchestration-script status. Two modules land here,
in two independently-owned plans:

- plan 22-02 ships ``accountant.py`` — the analytic Gaussian mechanism (Balle-Wang Thm 8) forward
  and inverse, importing stdlib ``math`` ONLY (D-10, DPSGD-03), so ``pyproject.toml`` stays
  untouched and RPT-03's zero-new-dependency streak holds.
- plan 22-04 ships ``dpsgd.py`` — the per-record clip + Gaussian noise mechanism (torch), whose
  constants are captured once in ``__init__`` and never re-sourced (D-15/D-17).

**There are deliberately NO re-exports and no ``__all__`` here**, which is where this file departs
from ``continual/__init__.py``'s form. The two modules arrive in two plans that execute in
different waves, so a re-exporting init would make this file a SHARED WRITE TARGET across parallel
waves — a merge conflict manufactured for the sake of a shorter import line. Consumers use the full
module path::

    from personacore.privacy.accountant import epsilon_for

That also keeps ``tests/test_phase22_accountant.py``'s V-09 import-walk honest: it asserts
``accountant.py``'s own imports are exactly ``{"math"}``, and a re-export would put a relative
``ImportFrom`` in the PACKAGE that a careless widening of that guard's scope would then have to
excuse.
"""
