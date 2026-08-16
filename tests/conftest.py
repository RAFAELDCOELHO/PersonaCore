"""Shared test fixtures — Pascal/P100 device simulation, and a deterministic stand-in model."""

import pytest

# The mixing constants behind ``fake_lm``'s logit surface. Knuth's multiplicative hash on the token
# id, a coprime stride across the vocab axis, and a prime modulus — an integer permutation, so the
# scores are spread across the whole ``[0, _SPREAD)`` band rather than clustered. ``_SPREAD = 4.0``
# is the one TUNED number: it sets how peaked the softmax is, and it is set wide enough that
# ``SAMPLE_TEMPERATURE=0.8`` + ``SAMPLE_TOP_P=0.95`` still leaves a large nucleus. That matters —
# a fake model whose nucleus collapses to one token would make every draw identical and D-09's
# prefix-stability assertion vacuously true. Measured at these values: 64 draws from one prompt
# are 64 DISTINCT completions, and 8 of them terminate on a ``STOP_IDS`` member.
_HASH_MULT = 2654435761
_HASH_STRIDE = 40503
_HASH_OFFSET = 12345
_HASH_MOD = 65521
_SPREAD = 4.0


@pytest.fixture
def simulate_pascal(monkeypatch):
    """Make torch report an available CUDA device with Pascal compute capability (6, 0).

    Lets the bf16-on-Pascal guard be tested on a CPU-only box (CI, laptop).
    """
    import torch

    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "get_device_capability", lambda *a, **k: (6, 0))
    return monkeypatch


@pytest.fixture
def fake_lm():
    """A parameter-free, bit-deterministic stand-in for the 13.9M model, on CPU.

    Satisfies the ``gpt.py:195-213`` contract exactly — ``forward(idx, targets=None)`` returns
    ``(logits, loss)`` with ``logits`` shaped ``(B, T, V)`` and ``loss`` ``None`` when ``targets``
    is ``None``, otherwise the identical flattened ``F.cross_entropy``. It carries a real
    ``ModelConfig()``, so ``vocab_size=8192`` spans the pinned ``STOP_IDS`` (8184, 8185) and the
    role ids, and ``block_size``/``eos_id`` are the values the generation core reads rather than
    a second transcription of them.

    Two guards exist to be testable on a box with no GPU, and both need a model that answers
    without a checkpoint:

    * **D-09 — prefix stability.** Family zero spends 9 draws while the attacks spend 64, so the
      control only controls the attacks if the 9-draw run is a byte-identical PREFIX of the
      64-draw run of the same loop. That is a claim about ``draw_all``'s code path, provable only
      by running it (``tests/test_phase18_draws.py``).
    * **D-29 / D-30 — the span-NLL reductions.** The sum-vs-mean choice and the taught-frame
      conditioning are read off a ``targets=``-bearing forward pass, which is why the loss branch
      is implemented here rather than left to raise.

    **Parameter-free and RNG-free by construction.** The logits are a pure integer hash of the
    input ids (see the module constants), so two calls on the same ids return tensors satisfying
    ``torch.equal``, and the ONLY randomness reaching a sampled draw is the ``torch.Generator``
    under test. A fixture holding ``nn.Parameter``s would have to be seeded, and a fixture that
    seeded itself would be indistinguishable from the thing the D-09 test is trying to measure.

    Scope, stated plainly: this models the SHAPE and the determinism of a trained model, not its
    behaviour. Its logit surface is a hash, not language — fine for the loop-level and
    reduction-level guards above, useless for anything that reads what the text says.
    """
    import torch
    import torch.nn.functional as F

    from personacore.config import ModelConfig

    class _HashLM(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.config = ModelConfig()

        def forward(self, idx, targets=None):
            vocab = torch.arange(self.config.vocab_size, device=idx.device)
            # (B, T, 1) broadcast against (V,) -> (B, T, V), int64 throughout so the hash is
            # exact: a float intermediate would round and stop being reproducible across builds.
            scores = idx.unsqueeze(-1) * _HASH_MULT + vocab * _HASH_STRIDE + _HASH_OFFSET
            logits = (scores % _HASH_MOD).to(torch.float32) * (_SPREAD / _HASH_MOD)
            if targets is None:
                return logits, None
            B, T, V = logits.shape
            loss = F.cross_entropy(logits.view(B * T, V), targets.view(B * T))
            return logits, loss

    return _HashLM()
