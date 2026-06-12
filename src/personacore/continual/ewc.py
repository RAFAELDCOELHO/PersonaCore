"""EWC quadratic penalty — the Kirkpatrick et al. 2017 (PNAS) form (EWC-02).

``EWCPenalty`` is a callable ``(model) -> scalar tensor`` computing
``(lam / 2) * sum_n (F_n * (theta_n - theta_star_n) ** 2).sum()`` over the named parameters —
the diagonal-Fisher quadratic anchor that penalizes drift away from ``theta_star``
proportionally to each coordinate's estimated importance.

Load-bearing properties:

- **Exact zero at the anchor:** ``theta_star`` entries are detached clones of the anchor
  params, so when ``p == theta_star`` bitwise the fp32 subtraction is exactly zero and the
  penalty is exactly ``0.0`` for any lambda and any Fisher — testable with ``==``, not
  allclose.
- **The assemble_loss / D-04 seam contract:** the returned value is a PRECOMPUTED scalar
  tensor on the model's device, differentiable w.r.t. the live params (Fisher/theta_star are
  constant buffers — no grad flows into them). The training loop passes
  ``(penalty_fn(model),)`` into ``assemble_loss`` — no callbacks, no lazy callables in the
  tuple.
- **Fail-loud validation at the choke points** (checkpoint.py ``load_adapter`` style): key
  and shape mismatches between ``fisher`` and ``theta_star`` raise ``ValueError`` naming the
  offending keys at CONSTRUCTION; a fisher key absent from ``model.named_parameters()`` —
  or present with a different shape than the live param — raises at CALL time — never a
  bare ``KeyError`` (or a silent broadcast) mid-run.
- **Device moved exactly ONCE:** both dicts are moved to ``device`` in ``__init__``
  (cross-device tensors crash mid-run on MPS — ARCHITECTURE anti-pattern 4).
- **Deterministic and RNG-free:** the penalty consumes no RNG and is a pure function of the
  params, so the resume-equality contract survives.
"""

__all__ = ["EWCPenalty"]


class EWCPenalty:
    """``(lam/2) * sum_n (F_n * (p_n - theta_star_n)**2).sum()`` — EWC-02."""

    def __init__(self, fisher, theta_star, lam, device):
        f_keys, t_keys = set(fisher.keys()), set(theta_star.keys())
        if f_keys != t_keys:
            raise ValueError(
                f"EWCPenalty: fisher/theta_star key mismatch — offending keys "
                f"{sorted(f_keys ^ t_keys)} (both dicts must be snapshot from the same "
                "model.named_parameters())."
            )
        if not fisher:
            raise ValueError("EWCPenalty: empty fisher/theta_star — nothing to anchor.")
        for name in fisher:
            if fisher[name].shape != theta_star[name].shape:
                raise ValueError(
                    f"EWCPenalty: shape mismatch for key {name!r}: fisher "
                    f"{tuple(fisher[name].shape)} vs theta_star "
                    f"{tuple(theta_star[name].shape)}."
                )
        # Moved to device exactly ONCE at construction (anti-pattern 4: cross-device
        # tensors against an MPS model crash mid-run).
        self.fisher = {n: f.to(device) for n, f in fisher.items()}
        self.theta_star = {n: t.to(device) for n, t in theta_star.items()}
        self.lam = lam

    def __call__(self, model):
        params = dict(model.named_parameters())  # ~100 entries — negligible per call.
        missing = sorted(self.fisher.keys() - params.keys())
        if missing:
            raise ValueError(
                f"EWCPenalty: fisher keys missing from model.named_parameters(): {missing} "
                "(was the penalty built for a different architecture?)."
            )
        # Shape check against the LIVE model: a same-named param of a different shape would
        # otherwise silently broadcast into a wrong penalty (or die as an anonymous mid-run
        # RuntimeError when non-broadcastable) — fail loud HERE, the choke point.
        mismatched = sorted(n for n, f in self.fisher.items() if params[n].shape != f.shape)
        if mismatched:
            raise ValueError(
                f"EWCPenalty: model parameter shape mismatch for keys {mismatched} "
                "(was the penalty built for a different architecture?)."
            )
        total = None
        for name, f in self.fisher.items():
            d = params[name] - self.theta_star[name]  # exactly 0.0 at the anchor (fp32).
            term = (f * d * d).sum()
            total = term if total is None else total + term
        return (self.lam / 2.0) * total  # scalar tensor; grads flow to the live params only.
