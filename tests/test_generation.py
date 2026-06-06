"""RED test surface for the Phase-6 generation toolkit (GEN-01 / GEN-02 / GEN-03).

CPU-only, GPU/MPS-free — the whole suite runs on a tiny in-memory ``GPT`` fixture
(``block_size=8, vocab_size=16, eos_id=15``), never a trained checkpoint or vocab file.

Posture (06-02 — all live):
  - The three GEN-01 sampling tests (``test_top_k_top_p_support``, ``test_temperature``,
    ``test_top_p_nucleus_exact``) exercise the pure transforms from
    ``personacore.generation.sampling`` (06-01).
  - The five GEN-02/GEN-03 core tests exercise ``personacore.generation.generate`` /
    ``collect`` (``core.py``, 06-02): EOS-stop, context-crop, output-shape, greedy and
    seeded determinism. No skips remain — the full suite runs on the tiny CPU fixture.

Determinism idioms (06-VALIDATION.md): seed-first ``torch.manual_seed`` for greedy;
isolated ``torch.Generator().manual_seed(0)`` for sampled (the global RNG is mutated by
``load_checkpoint``, so seeded sampling must never lean on it).
"""

import torch

from personacore.config import ModelConfig
from personacore.generation import collect
from personacore.generation.sampling import (
    apply_temperature,
    top_k_filter,
    top_p_filter,
)


def _tiny_model():
    """A minimal CPU GPT for fast generation tests — never a trained checkpoint.

    eos_id MUST be < vocab_size (15 < 16) and block_size small (8) so the crop test can
    cheaply exceed it. Tests read block_size/eos_id from ``model.config``, never hardcode.
    """
    return GPT(
        ModelConfig(
            block_size=8,
            vocab_size=16,
            n_layer=1,
            n_head=1,
            n_embd=8,
            eos_id=15,
        )
    )


# Imported lazily so the GEN-01 sampling tests do not require the model package to import.
try:
    from personacore.model import GPT
except ImportError:  # pragma: no cover - model package already shipped (Phase 4)
    GPT = None


# --------------------------------------------------------------------------- #
# GEN-01 — pure sampling transforms (GREEN after Task 2)
# --------------------------------------------------------------------------- #


def test_top_k_top_p_support():
    # top_k_filter leaves exactly k finite logits; top_p_filter leaves only the nucleus.
    logits = torch.tensor([[3.0, 2.0, 1.0, 0.0, -1.0]])

    k = 2
    filtered_k = top_k_filter(logits, k)
    finite_k = torch.isfinite(filtered_k)
    assert int(finite_k.sum()) == k
    # The k survivors are the top-k logits (3.0, 2.0).
    assert finite_k[0, 0] and finite_k[0, 1]

    # softmax probs ~ [0.6364, 0.2341, 0.0861, 0.0317, 0.0117]; p=0.8 -> nucleus = top-2.
    filtered_p = top_p_filter(logits, 0.8)
    finite_p = torch.isfinite(filtered_p)
    assert int(finite_p.sum()) == 2
    assert finite_p[0, 0] and finite_p[0, 1]


def test_temperature():
    # A near-zero temperature collapses the softmax mass onto the original argmax token.
    logits = torch.tensor([[1.0, 2.0, 3.0, 0.5]])
    original_argmax = int(torch.argmax(logits, dim=-1))

    scaled = apply_temperature(logits, 0.01)
    probs = torch.softmax(scaled, dim=-1)
    assert int(torch.argmax(probs, dim=-1)) == original_argmax
    assert float(probs[0, original_argmax]) > 0.9


def test_top_p_nucleus_exact():
    # HAND-COMPUTED: pick logits whose softmax probs are exactly [0.5, 0.3, 0.15, 0.05].
    # With p=0.8 the cumulative mass is 0.5, 0.8, 0.95, 1.0; the nucleus (kept set) is the
    # top-2 tokens (the second token lands exactly on the 0.8 boundary and is kept; the
    # third pushes past 0.8 and is masked). Pins assumption A1 (top-p off-by-one).
    probs = torch.tensor([0.5, 0.3, 0.15, 0.05])
    logits = torch.log(probs).unsqueeze(0)  # log-probs reproduce the target softmax exactly.

    filtered = top_p_filter(logits, 0.8)
    finite = torch.isfinite(filtered)
    expected_kept = torch.tensor([[True, True, False, False]])
    assert torch.equal(finite, expected_kept), f"nucleus mismatch: {finite.tolist()}"


# --------------------------------------------------------------------------- #
# GEN-02 — EOS-stop + context crop (skip-with-reason until core.py / 06-02)
# --------------------------------------------------------------------------- #


def test_eos_stop():
    # Force eos_id to be the argmax at a known step; generation must stop there and the
    # returned sequence must NOT end in eos_id (the core halts WITHOUT yielding EOS).
    model = _tiny_model()
    eos_id = model.config.eos_id

    def _forward(idx, targets=None):
        # Make eos_id the argmax for every position so the very first step would emit EOS.
        logits = torch.full((idx.size(0), idx.size(1), model.config.vocab_size), -1e9)
        logits[..., eos_id] = 1e9
        return logits, None

    model.forward = _forward  # type: ignore[method-assign]
    prompt = torch.tensor([[1, 2, 3]])
    out = collect(model, prompt, max_new_tokens=5, greedy=True)
    assert out[0, -1].item() != eos_id
    # Nothing was appended because the first (and only) candidate token was EOS.
    assert out.shape[1] == prompt.shape[1]


def test_past_block_size_no_crash():
    # Generating beyond block_size must crop the context (gpt.py:190 assert) and not raise.
    model = _tiny_model()
    block_size = model.config.block_size
    prompt = torch.tensor([[1, 2, 3]])
    n = block_size + 4  # forces at least one crop.
    out = collect(model, prompt, max_new_tokens=n, greedy=True)
    assert out.shape[1] == prompt.shape[1] + n


# --------------------------------------------------------------------------- #
# GEN-03 — output shape + determinism (skip-with-reason until core.py / 06-02)
# --------------------------------------------------------------------------- #


def test_output_shape():
    # collect() returns (1, prompt_len + n) LongTensor with no EOS in the body.
    # Seed the model init so the greedy argmax never lands on eos_id within n steps —
    # an unseeded tiny model can argmax to eos_id under a perturbed global RNG (an earlier
    # test mutates it), which would trim the output and make this shape assert order-dependent
    # (Pitfall 2 — global-RNG flakiness). manual_seed before construction fixes the weights.
    torch.manual_seed(1)
    model = _tiny_model()
    prompt = torch.tensor([[1, 2, 3]])
    n = 4
    out = collect(model, prompt, max_new_tokens=n, greedy=True)
    assert out.shape == (1, prompt.shape[1] + n)
    assert out.dtype == torch.long
    assert (out != model.config.eos_id).all()


def test_greedy_deterministic():
    # Two greedy (argmax) runs are bit-identical; no Generator needed (argmax has no RNG).
    torch.manual_seed(1337)
    model = _tiny_model()
    prompt = torch.tensor([[1, 2, 3]])
    out_a = collect(model, prompt, max_new_tokens=5, greedy=True)
    out_b = collect(model, prompt, max_new_tokens=5, greedy=True)
    assert torch.equal(out_a, out_b)


def test_seeded_sampling_deterministic():
    # Two identically-seeded torch.Generator runs match — seed isolation from the global RNG
    # (load_checkpoint mutates the global state, so seeded sampling must use a Generator).
    model = _tiny_model()
    prompt = torch.tensor([[1, 2, 3]])
    g1 = torch.Generator().manual_seed(0)
    g2 = torch.Generator().manual_seed(0)
    out_a = collect(model, prompt, max_new_tokens=5, temperature=1.0, generator=g1)
    out_b = collect(model, prompt, max_new_tokens=5, temperature=1.0, generator=g2)
    assert torch.equal(out_a, out_b)
