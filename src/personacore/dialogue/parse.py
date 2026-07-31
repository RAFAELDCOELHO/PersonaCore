"""From-scratch fb-dialog episode parser (DATA-01) — stdlib only.

ParlAI fb-dialog text is a sequence of numbered lines: ``N your persona: <sentence>`` persona
lines followed by ``N user_utt\\tassistant_reply\\t\\tcandidates`` dialogue lines; the line
number resetting to ``1`` is the ONLY episode boundary signal. Verified corpus properties
(2026-07-31 full-file scan): 8,939 train / 1,000 valid episodes, every dialogue line exactly
4 tab-fields (0 exceptions in 73,520 lines), 3-5 persona lines per episode. The retrieval
candidates field is ignored (D-04). The LAST episode has no trailing boundary line and must
be flushed at EOF (Pitfall 5). Persona text is returned RAW — including the ``!.`` artifact —
normalization belongs to the detokenizer (D-06), not the parser.
"""


def parse_episodes(path):
    """Parse an fb-dialog file into ``[(persona, turns), ...]`` episodes.

    ``persona`` is the ordered list of persona sentences (``"your persona: "`` prefix
    stripped); ``turns`` is the ordered list of ``(user, assistant)`` utterance pairs.
    Dialogue lines MUST carry exactly 4 tab-fields — the verified corpus invariant — so a
    malformed line hard-fails the unpack rather than silently mis-parsing. Zero-turn
    (persona-only) episodes — e.g. a file truncated right after persona lines — raise a
    ``ValueError`` here at the shared boundary, so neither the inflation gate nor the bin
    builder ever consumes a degenerate episode.
    """
    episodes = []
    persona, turns = [], []
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line.strip():  # defensive: stray blank lines never reach split("\t")
                continue
            num, _, rest = line.partition(" ")
            if num == "1" and (persona or turns):  # line-number reset = new episode
                if not turns:
                    raise ValueError(
                        f"{path}: episode ending before line {lineno} has persona but no turns"
                    )
                episodes.append((persona, turns))
                persona, turns = [], []
            if rest.startswith("your persona: "):
                persona.append(rest[len("your persona: ") :])
            else:
                user, reply, _, _cands = rest.split("\t")  # exactly 4 fields (verified)
                turns.append((user, reply))  # candidates ignored (D-04)
    if persona or turns:  # flush-at-EOF: the final episode has no trailing boundary (Pitfall 5)
        if not turns:
            raise ValueError(f"{path}: final episode has persona but no turns")
        episodes.append((persona, turns))
    return episodes
