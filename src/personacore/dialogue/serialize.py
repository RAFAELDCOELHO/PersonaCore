"""Dialogue serialization (DATA-02): detokenizer (D-06), renderer (D-04), mask encoder (D-01).

``encode_dialogue`` is the SINGLE source of truth for dialogue tokenization — the inflation
gate and the bin builder both consume it, so they can never tokenize differently (Pitfall 4).
Role/eos ids come from the LOCKED ``SPECIAL_TOKENS`` registry — never retyped (Don't-Hand-Roll).
Mask construction is SPAN-WISE: content spans are encoded with ``allowed_special="none"`` and
role ids appended literally, so mask offsets are exact by construction — never
encode-whole-then-search (the Pitfall-14 DataCollator failure mode). D-01 semantics: mask=1
on assistant content AND the turn's stop token (the next ``<|user|>``, or eos at dialogue
end) so the model trains to emit its own stop.
"""

import re

from personacore.tokenizer.special import EOS_ID, SPECIAL_TOKENS

_USER = "<|user|>"
_ASSISTANT = "<|assistant|>"
_SYSTEM = "<|system|>"

# " n't" attaches to the preceding word ("do n't" -> "don't"): PTB form, no-op on the primary
# fb-dialog corpus (zero apostrophes verified) but locked in D-06 for the JSON fallback.
_NT_RE = re.compile(r" +n't\b")
# Split apostrophe-suffix forms ("i ' m", "i 'm" -> "i'm"), optional spaces around the quote.
_APOS_RE = re.compile(r" *' *(m|s|re|ve|ll|d)\b")
# Space before closing punctuation ("thanks !" -> "thanks!").
_PUNCT_RE = re.compile(r" +([.,!?;:])")


def detokenize(text):
    """Minimal from-scratch normalizer (D-06): lowercase in, lowercase out (no truecasing).

    Rejoins split contractions, closes space-before-punctuation, and normalizes the ``!.``
    persona artifact (280 train lines, RESEARCH Open Q2) to ``!``.
    """
    text = _NT_RE.sub("n't", text)
    text = _APOS_RE.sub(r"'\1", text)
    text = _PUNCT_RE.sub(r"\1", text)
    return text.replace("!.", "!")


def render_document(persona, turns):
    """D-04 string form: ``<|system|>`` + newline-joined persona + role-token turn spans.

    NO space after role tokens (Pitfall 4 — matches the research smoke) and NO trailing eos
    marker: the string form feeds word-count denominators, not the encoder. Callers pass
    already-detokenized text.
    """
    parts = [_SYSTEM + "\n".join(persona)]
    for user, reply in turns:
        parts.append(_USER + user + _ASSISTANT + reply)
    return "".join(parts)


def encode_dialogue(tok, persona, turns):
    """Span-wise encode of one episode -> equal-length ``(ids, mask)`` with D-01 semantics.

    Applies ``detokenize`` to every content span itself, so gate and bins get identical
    tokenization (Pitfall 4). Role/eos ids are appended literally from the registry; content
    spans use ``tok.encode(text, allowed_special="none")`` so a literal marker in raw text
    byte-splits into ordinary tokens instead of injecting a control id (true by construction).
    Mask: persona=0, first ``<|user|>``=0 (opens the dialogue), every subsequent ``<|user|>``=1
    (stop token of the prior assistant turn), user content=0, ``<|assistant|>`` trigger=0,
    assistant content=1, final eos=1 (every episode ends on an assistant reply — verified).
    """
    user_id = SPECIAL_TOKENS[_USER]
    assistant_id = SPECIAL_TOKENS[_ASSISTANT]
    system_id = SPECIAL_TOKENS[_SYSTEM]
    ids, mask = [], []

    def emit(token_ids, m):
        ids.extend(token_ids)
        mask.extend([m] * len(token_ids))

    emit([system_id], 0)
    emit(tok.encode("\n".join(detokenize(p) for p in persona), allowed_special="none"), 0)
    for i, (user, reply) in enumerate(turns):
        emit([user_id], 1 if i > 0 else 0)
        emit(tok.encode(detokenize(user), allowed_special="none"), 0)
        emit([assistant_id], 0)
        emit(tok.encode(detokenize(reply), allowed_special="none"), 1)
    emit([EOS_ID], 1)
    return ids, mask
