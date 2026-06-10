"""Thin ``str -> str`` text wrapper over the id-space decode core (GEN-01 / GEN-02).

This is the surface the Phase-8 Gradio demo calls (D-01). It mirrors the training loop's
periodic sample hook (``training/loop.py`` ~L377-380): seed with the document-start token,
drive the core, decode, and show text — but as a streaming generator suitable for a chat UI.

Layering (one function, three consumers — D-04): the id-space :func:`generate` /
:func:`collect` core (06-02) serves the GEN-03 tests and Phase-7 eval; this wrapper serves
the demo. Both go through a single decode path.

Key decisions:
  - D-03: prepend ``[eos_id]`` to match the trained document-start register; an empty prompt
    falls back to exactly ``[eos_id]`` (the free-running seed the training sample hook uses).
  - D-02: only the continuation is returned — the prompt is stripped (the running buffer holds
    NEW ids only).
  - D-05: the core stops on EOS WITHOUT yielding it, so the raw ``<|endoftext|>`` separator
    never appears in the output.
  - D-06: decode the WHOLE running buffer each step and yield only the new string suffix. The
    tokenizer's decode is strict UTF-8 over a cumulative buffer, so a multi-byte glyph split
    across two byte-level-BPE ids surfaces once — never as mojibake or a strict-decode crash.
"""

import torch

from .core import generate

# DoS guard (V5 / T-06-04): an integer loop bound on generation. Rejected before the loop.
DEFAULT_MAX_NEW_TOKENS_CAP = 4096


def _model_device(model):
    """Resolve the device ``idx`` must land on so generation works on CPU and MPS alike."""
    try:
        return next(model.parameters()).device
    except StopIteration:  # pragma: no cover - a real GPT always has parameters.
        return torch.device("cpu")


def generate_text(
    model,
    tokenizer,
    prompt,
    *,
    eos_id=None,
    max_new_tokens,
    max_new_tokens_cap=DEFAULT_MAX_NEW_TOKENS_CAP,
    **gen_kw,
):
    """Stream the continuation of ``prompt`` as a sequence of new-text suffixes.

    Encodes the prompt as ``[eos_id] + tokenizer.encode(prompt)`` (an empty/falsy prompt seeds
    exactly ``[eos_id]`` — D-03), drives the id-space core, and yields the NEW string suffix at
    each step. Internally it accumulates only the NEW ids into a running buffer, decodes the
    whole buffer each step (D-06), and yields ``text[len(emitted):]`` — so the prompt is stripped
    (D-02) and multi-byte glyphs never appear as mojibake. The core stops on EOS without yielding
    it (D-05), so the raw separator never reaches the output.

    ``max_new_tokens`` is required and bounded: a value ``> max_new_tokens_cap`` or ``<= 0``
    raises :class:`ValueError` before the loop (V5 / T-06-04 DoS guard). Remaining ``gen_kw``
    (``temperature``, ``top_k``, ``top_p``, ``greedy``, ``generator``, ``block_size``) thread
    through to :func:`personacore.generation.core.generate`.

    Single-sequence only. ``eos_id`` defaults from ``model.config.eos_id`` (never hardcoded).
    """
    eid = eos_id if eos_id is not None else model.config.eos_id

    if max_new_tokens <= 0 or max_new_tokens > max_new_tokens_cap:
        raise ValueError(
            f"max_new_tokens must be in (0, {max_new_tokens_cap}], got {max_new_tokens!r}"
        )

    prompt_ids = [eid] + (tokenizer.encode(prompt) if prompt else [])
    idx = torch.tensor([prompt_ids], dtype=torch.long, device=_model_device(model))

    model.eval()  # inference posture (the core is already @torch.no_grad()).

    emitted = ""
    buffer_ids = []  # NEW ids only — the prompt is never decoded back out (D-02).
    for tok in generate(model, idx, eos_id=eid, max_new_tokens=max_new_tokens, **gen_kw):
        buffer_ids.append(tok)
        # Decode the WHOLE running buffer each step (D-06). A byte-level-BPE glyph can span
        # several ids, so a cumulative buffer that ends mid-glyph is NOT a defect — the strict
        # decoder raises UnicodeDecodeError on those trailing partial bytes (Pitfall 3). Hold the
        # ids and try again next step; the glyph surfaces once its final id arrives. This keeps
        # the buffer cumulative (never reset), so the delta below stays correct.
        try:
            text = tokenizer.decode(buffer_ids)
        except UnicodeDecodeError:
            continue  # partial multi-byte glyph — wait for the next id (no mojibake, no crash).
        new = text[len(emitted) :]
        emitted = text
        if new:
            yield new


def generate_text_str(model, tokenizer, prompt, **kw):
    """Non-streaming convenience: the full continuation string.

    One implementation, both uses (mirrors ``core.generate`` / ``core.collect``): joins the
    streamed suffixes into the complete continuation (prompt stripped, no raw EOS).
    """
    return "".join(generate_text(model, tokenizer, prompt, **kw))


def generate_text_cumulative(model, tokenizer, prompt, *, max_new_tokens, **gen_kw):
    """Stream the continuation as a GROWING cumulative string — the Gradio yield shape (DEMO-01).

    Pure adapter over :func:`generate_text`: accumulates each delta into a running string and
    yields the running string after every delta. The two yield shapes exist because they serve
    different consumers: ``generate_text`` yields DELTAS (the composable producer — join them,
    pipe them, measure them), while Gradio's ``ChatInterface`` REPLACES the displayed message
    with each yield, so its callback must yield the FULL cumulative response (08-RESEARCH
    Pitfall 1: yielding deltas makes the chat bubble flicker lone fragments instead of growing).

    Same contract as the producer otherwise: ``max_new_tokens`` is keyword-only and bounded to
    (0, ``max_new_tokens_cap``] (V5 / T-06-04 DoS guard fires before the loop); ``gen_kw``
    (``temperature``, ``top_k``, ``top_p``, ``greedy``, ``generator``, ``eos_id``) threads
    through unchanged; the prompt is stripped and the raw EOS separator never appears.
    """
    acc = ""
    for delta in generate_text(model, tokenizer, prompt, max_new_tokens=max_new_tokens, **gen_kw):
        acc += delta
        yield acc
