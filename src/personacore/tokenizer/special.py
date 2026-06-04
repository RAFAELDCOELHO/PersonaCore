"""Special-token registry (TOK-03, D-02 / D-03 / D-03a).

The 8 special tokens are pinned at the TOP of the 8192 vocab (ids 8184-8191). They are atomic:
split FIRST and NEVER byte-split or merged across (D-03 / RESEARCH Pattern 4). The set, count
(8), and ids are LOCKED here — ``<|endoftext|>`` is the single shared EOS id (8184), mirrored
into ``ModelConfig.eos_id`` so checkpoint and tokenizer agree. Most are reserved-now / dead
during M1 (the chat-role + pad + reserved slots earn their keep in M2), but the layout is fixed
now so token ids never move once training starts.
"""

# Vocab id partition (8192 total): bytes = 0-255, learned merges = 256-8183, specials = 8184-8191.
# Locked here (D-02/D-03a): the set, count (8), and ids are frozen; EOS is the single shared id.
EOS_TOKEN = "<|endoftext|>"

SPECIAL_TOKENS = {  # name -> id, ordered, top-pinned, fixed (Pitfall 5).
    "<|endoftext|>": 8184,
    "<|user|>": 8185,
    "<|assistant|>": 8186,
    "<|system|>": 8187,
    "<|pad|>": 8188,
    "<|reserved_0|>": 8189,
    "<|reserved_1|>": 8190,
    "<|reserved_2|>": 8191,
}

EOS_ID = SPECIAL_TOKENS[EOS_TOKEN]  # mirrored into ModelConfig.eos_id (D-03).
