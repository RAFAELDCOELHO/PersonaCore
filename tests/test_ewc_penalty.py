"""EWC quadratic-penalty tests (EWC-02 — the Kirkpatrick 2017 form).

CPU-only, GPU/MPS-free. Toy two-parameter modules with hand-computable values so every oracle
is explicit (test_assemble_loss.py exact-equality style).

Pinned behaviors:

  - test_quadratic_form_oracle — (lam/2) * sum(F * (p - theta_star)**2) matches a
    hand-computed literal within rtol=1e-7.
  - test_exact_zero_at_anchor — at theta_star = current params, penalty.item() == 0.0 with
    EXACT equality (bitwise-zero subtraction in fp32), not allclose (EWC-02).
  - test_lambda_linearity — penalty(lam=2) == 2 * penalty(lam=1) within rtol=1e-7 (powers of
    two scale exactly in fp32).
  - test_gradient_matches_analytic — d(penalty)/dp == lam * F * (p - theta_star).
  - test_construction_key_mismatch_raises — fisher/theta_star key mismatch raises ValueError
    naming the offending key at CONSTRUCTION (checkpoint.py load_adapter fail-loud style).
  - test_construction_shape_mismatch_raises — per-key shape mismatch raises ValueError
    naming the key.
  - test_call_missing_model_param_raises — a fisher key absent from model.named_parameters()
    raises ValueError naming the missing key when CALLED.
  - test_assemble_loss_integration — assemble_loss(base, (penalty,)) == base + penalty
    exactly (torch.equal, the D-04 seam contract) and .backward() populates grads on
    displaced params.
"""

import pytest
import torch

from personacore.continual import EWCPenalty
from personacore.training.loss import assemble_loss


class _Toy(torch.nn.Module):
    """Two named parameters ('w' 2x2, 'b' 2) — small enough for literal hand-computation."""

    def __init__(self, w, b):
        super().__init__()
        self.w = torch.nn.Parameter(w.clone())
        self.b = torch.nn.Parameter(b.clone())


def _toy_model():
    w = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
    b = torch.tensor([0.5, -0.5])
    return _Toy(w, b)


def _toy_fisher():
    return {
        "w": torch.tensor([[1.0, 0.5], [2.0, 1.0]]),
        "b": torch.tensor([4.0, 0.25]),
    }


def _toy_theta_star():
    return {
        "w": torch.tensor([[0.5, 1.0], [2.0, 5.0]]),
        "b": torch.tensor([0.0, 0.0]),
    }


def test_quadratic_form_oracle():
    # Hand computation: w - th = [[.5, 1], [1, -1]] -> sq [[.25, 1], [1, 1]] -> F*sq sums 3.75;
    # b - th = [.5, -.5] -> sq [.25, .25] -> F*sq sums 1.0625; total 4.8125;
    # (0.8 / 2) * 4.8125 = 1.925.
    penalty = EWCPenalty(_toy_fisher(), _toy_theta_star(), lam=0.8, device="cpu")(_toy_model())
    assert penalty.item() == pytest.approx(1.925, rel=1e-7)


def test_exact_zero_at_anchor():
    # EWC-02: theta_star cloned from the live params -> (p - theta_star) is bitwise zero in
    # fp32, so the penalty is EXACTLY 0.0 for any lam and any F — equality, NOT allclose.
    model = _toy_model()
    theta_star = {n: p.detach().clone() for n, p in model.named_parameters()}
    penalty = EWCPenalty(_toy_fisher(), theta_star, lam=123.4, device="cpu")(model)
    assert penalty.item() == 0.0


def test_lambda_linearity():
    # Powers of two scale exactly in fp32 -> doubling lam exactly doubles the penalty.
    model = _toy_model()
    p1 = EWCPenalty(_toy_fisher(), _toy_theta_star(), lam=1.0, device="cpu")(model)
    p2 = EWCPenalty(_toy_fisher(), _toy_theta_star(), lam=2.0, device="cpu")(model)
    assert p2.item() == pytest.approx(2.0 * p1.item(), rel=1e-7)


def test_gradient_matches_analytic():
    # d/dp of (lam/2) * F * (p - theta_star)^2 == lam * F * (p - theta_star).
    model = _toy_model()
    fisher, theta_star, lam = _toy_fisher(), _toy_theta_star(), 0.8
    penalty = EWCPenalty(fisher, theta_star, lam, device="cpu")(model)
    params = dict(model.named_parameters())
    grads = torch.autograd.grad(penalty, [params["w"], params["b"]])
    for name, g in zip(["w", "b"], grads):
        expected = lam * fisher[name] * (params[name].detach() - theta_star[name])
        assert torch.allclose(g, expected, rtol=1e-6, atol=0), name


def test_construction_key_mismatch_raises():
    # Fail-loud at construction, naming the offending key (load_adapter error style).
    fisher = dict(_toy_fisher(), extra_only_in_fisher=torch.tensor([1.0]))
    with pytest.raises(ValueError, match="extra_only_in_fisher"):
        EWCPenalty(fisher, _toy_theta_star(), lam=1.0, device="cpu")


def test_construction_shape_mismatch_raises():
    theta_star = _toy_theta_star()
    theta_star["b"] = torch.tensor([0.0, 0.0, 0.0])  # wrong shape for key 'b'.
    with pytest.raises(ValueError, match="b"):
        EWCPenalty(_toy_fisher(), theta_star, lam=1.0, device="cpu")


def test_call_missing_model_param_raises():
    # Keys agree between fisher and theta_star but name no model parameter -> the CALL fails
    # loudly naming the missing key, never a bare KeyError.
    fisher = {"nonexistent_param": torch.tensor([1.0])}
    theta_star = {"nonexistent_param": torch.tensor([0.0])}
    penalty = EWCPenalty(fisher, theta_star, lam=1.0, device="cpu")
    with pytest.raises(ValueError, match="nonexistent_param"):
        penalty(_toy_model())


def test_assemble_loss_integration():
    # The D-04 seam: the penalty is a PRECOMPUTED scalar tensor that assemble_loss adds
    # exactly; backward through the assembled total reaches the displaced params.
    model = _toy_model()
    base_loss = torch.tensor(2.0)
    penalty = EWCPenalty(_toy_fisher(), _toy_theta_star(), lam=0.8, device="cpu")(model)
    total = assemble_loss(base_loss, (penalty,))
    assert torch.equal(total, base_loss + penalty)
    total.backward()
    for name, p in model.named_parameters():
        assert p.grad is not None, name
        assert p.grad.abs().sum().item() > 0.0, name
