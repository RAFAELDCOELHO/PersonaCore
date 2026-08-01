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

from personacore.generation.text import undecodable_ids_mask


@torch.no_grad()
def perplexity(model, val_bin_path, block_size, device, batch_size=32, forbid_ids=None):
    """Deterministic full-corpus PPL over non-overlapping ``block_size`` windows.

    Args:
        model: a ``GPT`` whose ``forward(idx)`` returns ``(logits, loss)``.
        val_bin_path: path to a flat ``uint16`` token memmap.
        block_size: window stride; the model sees up to ``block_size`` tokens and
            scores the next-token transitions inside each window.
        device: torch device string/object the tensors are moved to.
        batch_size: accepted for signature parity with the data path; the sweep
            scores one window at a time, so it is unused here.
        forbid_ids: optional ``(1, vocab)`` bool tensor (DEBT-02); ``True`` ids are
            masked to ``-inf`` before the CE — the SAME semantics the generation path
            applies in ``sampling.next_token``. Default ``None`` preserves the v1.0
            unmasked headline semantics (the committed 2.1066 stays reproducible).
            Retention curves must NOT call this directly — use
            :func:`retention_perplexity`, the frozen policy wrapper.

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
        if forbid_ids is not None:
            logits = logits.masked_fill(forbid_ids.to(logits.device), float("-inf"))
        ce = F.cross_entropy(logits.view(-1, logits.size(-1)), y.view(-1), reduction="sum")
        total_ce += ce.item()
        total_tokens += y.numel()
    if total_tokens == 0:
        raise ValueError(
            f"perplexity(): no scorable tokens in {val_bin_path!r} "
            f"(corpus length {n}); need at least 2 tokens."
        )
    return math.exp(total_ce / total_tokens), total_tokens


@torch.no_grad()
def masked_perplexity(model, bin_path, mask_path, block_size, device, forbid_ids=None):
    """Masked dialogue-val PPL — THE frozen gate metric for all Phase-12 arms (TUNE-01).

    DECISION (frozen, pre-first-smoke): every D-01/D-02/D-05 gate comparison — masked
    arm, unmasked arm, EWC arm — is judged by THIS one deterministic number. The
    evaluation policy is fixed independently of the training arm (Pitfall 3
    incommensurability): arms may train different objectives, but they are all scored
    on assistant-token (mask==1) targets only, over the whole dialogue-val corpus, in
    the same non-overlapping-window sweep as :func:`perplexity`. ``estimate_loss``'s
    20-random-batch mean must NOT be used for gates — its eval sampling noise would
    pollute margins that measure training noise.

    The mask memmap (``uint8``) is 1:1 aligned with the token memmap and sliced SHIFTED
    with the targets (``mask[i+1:end]``), so token j's mask governs the prediction OF
    token j (target-space semantics — same as ``data.get_batch_memmap_masked``).
    ``mask==0`` targets become ``ignore_index=-100`` and contribute neither to the CE
    sum nor to the denominator.

    Raises:
        ValueError: on token/mask length mismatch (bins must be element-aligned) or
            when the mask scores zero shifted targets.

    Returns:
        ``(ppl, total_tokens)`` where ``ppl = exp(total_CE / total_tokens)`` and
        ``total_tokens`` is the exact count of mask==1 scored targets (auditable).
    """
    model.eval()
    # Re-open BOTH memmaps read-only per call (nanoGPT RSS-leak avoidance — data.py:84).
    data = np.memmap(bin_path, dtype=np.uint16, mode="r")
    mask = np.memmap(mask_path, dtype=np.uint8, mode="r")
    if len(data) != len(mask):
        raise ValueError(
            f"token/mask bin length mismatch: {bin_path} has {len(data)} elements but "
            f"{mask_path} has {len(mask)} — bins must be element-aligned (T-11-04)"
        )
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
        m = torch.from_numpy(mask[i + 1 : end].astype(np.int64)).to(device).unsqueeze(0)
        y = y.masked_fill(m == 0, -100)
        logits, _ = model(x)  # ignore the mean loss; recompute a SUM below
        if forbid_ids is not None:
            logits = logits.masked_fill(forbid_ids.to(logits.device), float("-inf"))
        ce = F.cross_entropy(
            logits.view(-1, logits.size(-1)), y.view(-1), reduction="sum", ignore_index=-100
        )
        total_ce += ce.item()
        total_tokens += int((y != -100).sum())
    if total_tokens == 0:
        raise ValueError(
            f"masked_perplexity(): zero scored targets in {bin_path!r} with mask "
            f"{mask_path!r} (corpus length {n}); mask==1 must cover at least one "
            f"shifted target."
        )
    return math.exp(total_ce / total_tokens), total_tokens


@torch.no_grad()
def retention_perplexity(model, val_bin_path, block_size, device, tokenizer, batch_size=32):
    """Retention PPL for forgetting curves — dead-id mask applied, policy FROZEN (DEBT-02).

    DECISION (frozen 2026-07-31, pre-Phase-12): every retention/forgetting-curve PPL point
    uses the SAME ``undecodable_ids_mask`` the generation path already applies (CR-01) —
    comparative-pair consistency inside the Phase 13 A/B matters more than comparability
    with raw PPL from other work, and the metric must reflect what the real system
    experiences (the same reason masking was adopted at generation time). This wrapper is
    THE ONLY sanctioned PPL for curve points; the unmasked :func:`perplexity` remains the
    v1.0 headline semantics (2.1066) and must not be used for retention curves.

    ``vocab_size`` is inferred from a 1-token probe forward so the wrapper stays
    duck-typed over any ``forward(idx) -> (logits, loss)`` model.

    Returns:
        ``(ppl, total_tokens)`` — same auditable contract as :func:`perplexity`.
    """
    probe = torch.zeros(1, 1, dtype=torch.long, device=device)
    logits, _ = model(probe)
    forbid_ids = undecodable_ids_mask(tokenizer, logits.size(-1))
    return perplexity(
        model, val_bin_path, block_size, device, batch_size=batch_size, forbid_ids=forbid_ids
    )
