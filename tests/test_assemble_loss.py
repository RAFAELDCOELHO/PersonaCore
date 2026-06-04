"""RED tests for the EWC-seam loss combiner (TRAIN-06 / D-04a).

``assemble_loss(base_loss, extra_penalties=())`` is the additive hook the M2 EWC penalty
plugs into with NO change to the training loop: with no penalties it is the IDENTITY on the
base loss, and with penalties it returns ``base + sum(penalties)``. Locking it now (as a RED
test) keeps continual-learning additive in Milestone 2.

RED until Plan 02 implements ``personacore.training.loss``. CPU-only, GPU-free.
"""

import torch

from personacore.training.loss import assemble_loss


def test_empty_is_identity():
    # No penalties -> the base loss passes through unchanged (the M1 path).
    x = torch.tensor(2.5)
    assert torch.equal(assemble_loss(x, ()), x)


def test_default_arg_is_identity():
    # The default empty extra_penalties keeps the loop's call site penalty-free.
    x = torch.tensor(3.0)
    assert torch.equal(assemble_loss(x), x)


def test_additive_with_single_penalty():
    # One penalty adds exactly (the EWC seam: base + lambda * fisher term).
    x, p = torch.tensor(2.0), torch.tensor(0.5)
    assert torch.equal(assemble_loss(x, (p,)), torch.tensor(2.5))


def test_additive_with_multiple_penalties():
    # sum over an arbitrary tuple of scalar penalties.
    x = torch.tensor(1.0)
    penalties = (torch.tensor(0.25), torch.tensor(0.75))
    assert torch.equal(assemble_loss(x, penalties), torch.tensor(2.0))
