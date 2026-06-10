"""Pure logit transforms for next-token sampling (GEN-01).

Four standalone, side-effect-free functions over a single-sequence last-position logit
tensor of shape ``(1, vocab)`` — no batch (scope fence for Phase 6). They compose, in the
locked order ``temperature -> top-k -> top-p -> softmax -> multinomial``, inside
:func:`next_token`; the richer ``generate``/``collect`` core that drives them step-by-step
arrives in 06-02. ``top_k`` and ``top_p`` STACK (apply both when both are set).

``top_k_filter`` is the verbatim nanoGPT idiom; ``top_p_filter`` is the standard
sort-cumsum-shift nucleus mask (RESEARCH Pattern 3, Pitfall 5) — both ``.clone()``
defensively so they never mutate the caller's tensor in place. The top-p off-by-one
(always keep the top-1 token; keep the boundary token that lands on ``p``) is pinned by
``tests/test_generation.py::test_top_p_nucleus_exact`` (assumption A1). GEN-01.
"""

import torch


def apply_temperature(logits, temperature):
    """Scale logits by ``1 / temperature`` (guarded against division by zero).

    A near-zero temperature sharpens the softmax toward the argmax token. ``temperature == 0``
    is handled as the greedy branch upstream in :func:`next_token`, not here, so the floor
    ``max(temperature, 1e-8)`` is only a safety guard against accidental zero/negative input.
    """
    return logits / max(temperature, 1e-8)


def top_k_filter(logits, k):
    """Keep the top ``min(k, vocab)`` logits finite, mask the rest to ``-inf``.

    Verbatim nanoGPT idiom with a defensive ``.clone()`` (standalone func — never mutate the
    caller's tensor in place).
    """
    k = min(k, logits.size(-1))
    v, _ = torch.topk(logits, k)
    out = logits.clone()
    out[out < v[:, [-1]]] = float("-inf")
    return out


def top_p_filter(logits, p):
    """Nucleus mask: keep the smallest token set whose cumulative softmax prob reaches ``p``.

    Sort descending, cumulative-sum the softmax, then mask tokens once the cumulative mass has
    EXCEEDED ``p`` — with a shift-right so the boundary token (the one that crosses ``p``) is
    kept and the top-1 token is never masked (Pitfall 5). The mask is scattered back to the
    original token order; a defensive ``masked_fill`` leaves the caller's tensor untouched.
    """
    sorted_logits, sorted_idx = torch.sort(logits, descending=True, dim=-1)
    cum_probs = torch.softmax(sorted_logits, dim=-1).cumsum(dim=-1)
    # ``>=`` so a token landing EXACTLY on the cumulative-``p`` boundary closes the nucleus
    # (it does not pull in the next token). On [0.5,0.3,0.15,0.05]/p=0.8 this keeps exactly
    # the top-2 (cum hits 0.8 at the 2nd token) — the A1 contract in test_top_p_nucleus_exact.
    sorted_mask = cum_probs >= p
    # Shift right: keep the boundary token, and never mask the highest-prob token.
    sorted_mask[..., 1:] = sorted_mask[..., :-1].clone()
    sorted_mask[..., 0] = False
    mask = sorted_mask.scatter(-1, sorted_idx, sorted_mask)
    return logits.masked_fill(mask, float("-inf"))


def next_token(
    logits_last,
    *,
    temperature=1.0,
    top_k=None,
    top_p=None,
    greedy=False,
    generator=None,
    forbid_ids=None,
):
    """Pick the next token id from a ``(1, vocab)`` last-position logit tensor.

    Greedy short-circuits to ``torch.argmax(..., keepdim=True)`` (a ``(1, 1)`` LongTensor, no
    RNG). Otherwise the locked composition runs: temperature scaling, then top-k, then top-p
    (both stack when set), then softmax, then ``torch.multinomial`` drawing one sample through
    the supplied ``generator`` (seed isolation — never the global RNG).

    ``forbid_ids`` is an optional bool tensor broadcastable to ``(1, vocab)``; ``True``
    entries are masked to ``-inf`` BEFORE the greedy argmax and BEFORE the
    temperature/top-k/top-p pipeline, so a forbidden id has exactly probability zero under
    ``torch.multinomial`` and can never be the argmax. Built by the demo from
    tokenizer-undecodable ids (CR-01 — the frozen production tokenizer decodes only 547 of
    the model's 8192 ids; sampling a dead id crashes the strict decoder mid-stream).
    ``masked_fill`` is non-mutating, so the caller's tensor is never touched.
    """
    if forbid_ids is not None:
        logits_last = logits_last.masked_fill(forbid_ids, float("-inf"))

    if greedy:
        return torch.argmax(logits_last, dim=-1, keepdim=True)

    logits = apply_temperature(logits_last, temperature)
    # top_k=0 (and negatives) is the common "disabled" idiom — treat as no-op
    # rather than threading a non-positive k into torch.topk, which crashes
    # mid-stream (top_k=0 -> IndexError, top_k<0 -> RuntimeError) on a shared path.
    if top_k is not None and top_k > 0:
        logits = top_k_filter(logits, top_k)
    if top_p is not None:
        logits = top_p_filter(logits, top_p)
    probs = torch.softmax(logits, dim=-1)
    return torch.multinomial(probs, num_samples=1, generator=generator)
