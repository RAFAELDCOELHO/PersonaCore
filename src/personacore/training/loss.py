"""Loop-level loss assembly — the M2 EWC seam (TRAIN-06 / D-03 / D-04).

``assemble_loss`` is the additive extension point the Milestone-2 EWC penalty plugs into with
ZERO changes to the training loop. In Milestone 1 the loop always passes ``()`` so it is the
IDENTITY on the base cross-entropy; in Milestone 2 EWC passes ``(fisher_penalty,)`` and the
total becomes ``base + sum(penalties)``.

Load-bearing property:
- D-03: loss assembly lives HERE, in ``training/``, never inside the model — the model stays a
  pure ``(logits, loss)`` producer. This separation is what keeps the Phase-4 GPT reusable
  unchanged and continual-learning additive in M2.
- D-04: identity-on-empty, additive-on-non-empty. Penalties are PRECOMPUTED scalar tensors
  (no callbacks, no lazy callables) so the seam carries no hidden control flow.
"""


def assemble_loss(base_loss, extra_penalties=()):
    """Return ``base_loss + sum(extra_penalties)`` — identity when ``extra_penalties`` is empty.

    Args:
        base_loss: The model's scalar cross-entropy (or any scalar tensor).
        extra_penalties: A tuple of precomputed scalar penalty tensors. Empty ``()`` in M1
            (identity); EWC supplies ``(fisher_penalty,)`` in M2 with no loop change (D-04).
    """
    total = base_loss
    for p in extra_penalties:
        total = total + p
    return total
