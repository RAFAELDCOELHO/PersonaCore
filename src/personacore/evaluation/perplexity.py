"""Deterministic full-corpus perplexity (EVAL-01).

The single canonical headline number (and every EVAL-03 ablation-cohort PPL cell)
flows through ``perplexity()``. Unlike ``training.loop.estimate_loss`` (20 random
batches -> a non-deterministic mean-of-means), this sweeps the WHOLE corpus once in
NON-OVERLAPPING ``block_size`` windows, sums cross-entropy over every predicted
token with ``reduction="sum"``, and exponentiates the grand total over the EXACT
auditable token count (D-01..D-03).

Accounting invariants (pinned by ``tests/test_perplexity.py``):
  - A length-L window predicts L-1 transitions: token 0 is context-only, never
    scored. So the denominator is ``corpus_len - n_windows`` (each scored window
    loses its first token as unpredictable).
  - The final partial window IS scored (it contributes ``len(chunk) - 1``
    transitions); a single dangling trailing token (``numel < 2``) is skipped.
  - ``reduction="sum"`` is MANDATORY — ``GPT.forward(targets=)`` returns a per-window
    MEAN loss (``gpt.py:203``); averaging per-window means would mis-weight the short
    final window. The model's returned loss is ignored entirely here.
  - Every predicted token counts, including inter-document ``eos_id`` — the model was
    trained that way, so it is NOT masked.
"""

import math

import numpy as np
import torch
import torch.nn.functional as F


@torch.no_grad()
def perplexity(model, val_bin_path, block_size, device, batch_size=32):
    """Deterministic full-corpus PPL over non-overlapping ``block_size`` windows.

    Args:
        model: a ``GPT`` whose ``forward(idx)`` returns ``(logits, loss)``.
        val_bin_path: path to a flat ``uint16`` token memmap.
        block_size: window stride; the model sees up to ``block_size`` tokens and
            scores the next-token transitions inside each window.
        device: torch device string/object the tensors are moved to.
        batch_size: accepted for signature parity with the data path; the sweep
            scores one window at a time, so it is unused here.

    Returns:
        ``(ppl, total_tokens)`` where ``ppl = exp(total_CE / total_tokens)`` and
        ``total_tokens`` is the exact denominator (D-03) so the number is auditable.
    """
    model.eval()
    # Re-open the memmap read-only per call (nanoGPT RSS-leak avoidance — data.py:84).
    data = np.memmap(val_bin_path, dtype=np.uint16, mode="r")
    n = len(data)
    total_ce = 0.0
    total_tokens = 0
    for i in range(0, n - 1, block_size):
        end = min(i + block_size + 1, n)  # +1 so the shifted target fits in the slice
        chunk = torch.from_numpy(data[i:end].astype(np.int64)).to(device)
        if chunk.numel() < 2:
            continue  # a single dangling token has nothing to predict
        x = chunk[:-1].unsqueeze(0)  # (1, T)
        y = chunk[1:].unsqueeze(0)  # (1, T)
        logits, _ = model(x)  # ignore the mean loss; recompute a SUM below
        ce = F.cross_entropy(
            logits.view(-1, logits.size(-1)), y.view(-1), reduction="sum"
        )
        total_ce += ce.item()
        total_tokens += y.numel()
    if total_tokens == 0:
        raise ValueError(
            f"perplexity(): no scorable tokens in {val_bin_path!r} "
            f"(corpus length {n}); need at least 2 tokens."
        )
    return math.exp(total_ce / total_tokens), total_tokens
