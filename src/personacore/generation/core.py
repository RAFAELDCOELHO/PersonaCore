"""Shared token-level generator core (GEN-01 / GEN-02).

One decoding implementation behind every consumer (D-04): the GEN-03 tests, the Phase-7
evaluation, and (via the 06-03 wrapper) the Phase-8 demo. :func:`generate` is an
``@torch.no_grad()`` Python generator that yields each new token id one step at a time;
:func:`collect` drains it into the full ``(1, prompt_len + n)`` LongTensor.

This SUPERSEDES ``training/loop.py::sample`` (D-11) — it keeps that idiom's
``@torch.no_grad()`` decorator, the ``for _ in range(max_new_tokens)`` bound, the
``logits[:, -1, :]`` slice and the ``torch.cat`` append, and ADDS the mandatory context
crop (``gpt.py:190`` asserts ``T <= block_size``), EOS-stop-without-yield (D-05), and the
delegation of the logit->id decision to :func:`personacore.generation.sampling.next_token`.
The training loop and its barrel are intentionally left untouched.

Single-sequence only (no batch — Phase-6 scope fence): ``idx`` is a ``(1, T)`` LongTensor.
``block_size`` and ``eos_id`` are read from ``model.config`` — never hardcoded.
"""

import torch

from .sampling import next_token


@torch.no_grad()
def generate(
    model,
    idx,
    *,
    max_new_tokens,
    eos_id=None,
    temperature=1.0,
    top_k=None,
    top_p=None,
    greedy=False,
    generator=None,
    block_size=None,
):
    """Yield each newly decoded token id, one step at a time.

    Loops at most ``max_new_tokens`` times. Each step crops the running context to the last
    ``block_size`` ids (so generating past ``block_size`` never trips ``gpt.py:190``), runs a
    forward pass, and delegates the logit->id decision to :func:`next_token`. If the chosen
    token is ``eos_id`` the generator RETURNS immediately — the EOS token is neither yielded
    nor appended (D-05), simultaneously satisfying GEN-02's "stop on EOS" and "trim the
    trailing token". ``block_size`` and ``eos_id`` default from ``model.config``.

    Greedy decoding (``greedy=True``) is deterministic (argmax, no RNG); the sampled path
    threads ``generator`` into :func:`next_token` for seeded reproducibility.
    """
    bs = block_size if block_size is not None else model.config.block_size
    eid = eos_id if eos_id is not None else model.config.eos_id

    for _ in range(max_new_tokens):
        idx_cond = idx if idx.size(1) <= bs else idx[:, -bs:]
        logits, _ = model(idx_cond)  # (B, T, V)
        next_id = next_token(
            logits[:, -1, :],
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            greedy=greedy,
            generator=generator,
        )
        tok = int(next_id)
        if tok == eid:
            return  # D-05 — stop on EOS WITHOUT yielding/appending it.
        idx = torch.cat([idx, next_id], dim=1)
        yield tok


def collect(model, idx, **kw):
    """Drain :func:`generate` into the full ``(1, prompt_len + n)`` LongTensor.

    Returns the prompt with all newly generated ids concatenated (D-02), preserving ``idx``'s
    dtype and device. ``n`` is the number of tokens emitted before EOS / ``max_new_tokens``.
    """
    out = idx
    for tok in generate(model, idx, **kw):
        out = torch.cat([out, torch.tensor([[tok]], dtype=out.dtype, device=out.device)], dim=1)
    return out
