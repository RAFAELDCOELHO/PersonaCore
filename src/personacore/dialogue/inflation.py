"""Tokenizer-inflation metrics for the DATA-04 gate (D-08) — one encode pass, four metrics.

Every metric flows through ``encode_dialogue`` — the SINGLE dialogue tokenization path the bin
builder also uses (Pitfall 4: gate and bins can never tokenize differently). Span boundaries
are recovered from the role-token ids in the encoded stream (role ids never occur inside
content spans — content is encoded with ``allowed_special="none"``, so a marker literal in
raw text byte-splits into ordinary tokens; the invariant holds by construction).
Each metric is returned WITH its auditable denominator (``evaluation.perplexity`` posture) so
the committed report's numbers can be re-derived.

D-08 metric set:
  1. ``tokens_per_word`` — utterance-span token count over the whitespace word count of the
     detokenized utterance text (user + assistant turns; persona and role tokens excluded from
     BOTH numerator and denominator).
  2. ``persona_cost`` — p50/p90/max of the persona-span cost per episode (``<|system|>`` token
     + persona ids), feeding the D-07 cap.
  3. ``fit_fraction`` — fraction of episodes where the persona span + the FULL first
     user->assistant exchange (all ids incl. role tokens and the exchange's stop token: the
     second ``<|user|>``, or eos for single-turn episodes) fits in ``block_size``. Replaces
     DATA-04's literal %-over-block_size per D-08's window-utility rationale.
  4. ``fragmentation`` — token counts for a FIXED word list (the research samples), so the
     committed numbers stay comparable across runs.
"""

import numpy as np

from personacore.tokenizer.special import SPECIAL_TOKENS

from .serialize import detokenize, encode_dialogue

_USER_ID = SPECIAL_TOKENS["<|user|>"]
_ASSISTANT_ID = SPECIAL_TOKENS["<|assistant|>"]

# Fixed qualitative-fragmentation probe words (research smoke samples — keep comparable).
FRAGMENTATION_SAMPLES = ("halloween", "cheetah", "remodel", "mermaids", "anchorage")


def compute_inflation_metrics(episodes, tok, block_size):
    """Compute the four D-08 metrics over ``episodes`` in one ``encode_dialogue`` pass each.

    Args:
        episodes: ``[(persona, turns), ...]`` as returned by ``parse_episodes``.
        tok: the FROZEN production tokenizer (never a fresh one — Pitfall 6).
        block_size: the training window (``ModelConfig.block_size``).

    Returns:
        dict with ``tokens_per_word`` (+ ``total_tokens``/``total_words`` denominators),
        ``persona_cost`` (p50/p90/max + ``episodes`` count), ``fit_fraction``
        (+ ``fit_count``/``episodes``), and ``fragmentation`` ({word: n_tokens}).
        Deterministic: no RNG anywhere.
    """
    total_tokens = 0
    total_words = 0
    persona_costs = []
    fit_count = 0

    for persona, turns in episodes:
        ids, _mask = encode_dialogue(tok, persona, turns)

        user_positions = [i for i, t in enumerate(ids) if t == _USER_ID]
        # Metric 2 denominator basis: everything before the first <|user|> is the persona span
        # (the <|system|> token + persona ids).
        persona_costs.append(user_positions[0])

        # Metric 3: persona + full first exchange incl. its stop token (second <|user|>, or
        # eos when the episode has a single turn — ids ends [..., reply, eos]).
        first_exchange_end = user_positions[1] + 1 if len(user_positions) > 1 else len(ids)
        if first_exchange_end <= block_size:
            fit_count += 1

        # Metric 1 numerator: utterance-content ids between consecutive role markers (the
        # final marker span is closed by eos at len(ids)-1). Persona ids are excluded — the
        # first marker starts the count.
        markers = [i for i, t in enumerate(ids) if t in (_USER_ID, _ASSISTANT_ID)]
        markers.append(len(ids) - 1)  # eos closes the last assistant span
        for start, end in zip(markers, markers[1:]):
            total_tokens += end - start - 1
        # Metric 1 denominator: whitespace words of the SAME detokenized utterance text the
        # encoder saw (detokenize applied identically — Pitfall 4).
        for user, reply in turns:
            total_words += len(detokenize(user).split()) + len(detokenize(reply).split())

    n_episodes = len(episodes)
    costs = np.asarray(persona_costs)
    return {
        "tokens_per_word": total_tokens / total_words,
        "total_tokens": total_tokens,
        "total_words": total_words,
        "persona_cost": {
            "p50": float(np.percentile(costs, 50)),
            "p90": float(np.percentile(costs, 90)),
            "max": int(costs.max()),
            "episodes": n_episodes,
        },
        "fit_fraction": fit_count / n_episodes,
        "fit_count": fit_count,
        "episodes": n_episodes,
        "fragmentation": {w: len(tok.encode(w)) for w in FRAGMENTATION_SAMPLES},
    }
