"""Per-example empirical diagonal Fisher tests (EWC-01 / D-01..D-05).

CPU-only, GPU/MPS-free. Pins ``estimate_fisher``'s estimation discipline on a tiny GPT fixture
(``ModelConfig(block_size=32, n_layer=1, n_head=2, n_embd=16)``, LOCKED vocab/eos defaults) and
a tmp uint16 ``.bin`` corpus. The window-draw pattern is itself part of the contract: one
``int(rng.integers(0, data_len - block_size - 1))`` call per example, in example order, from a
LOCAL ``np.random.default_rng(seed)`` — the oracle re-derives the exact windows from it.

Pinned behaviors:

  - test_per_example_oracle — the raw (normalize=False) Fisher matches a brute-force
    per-example loop (forward -> autograd.grad -> g**2, averaged over N) per-tensor (EWC-01).
  - test_differs_from_batched_gradient_estimate — on the SAME windows, the batched-gradient
    "Fisher" (one batch=N forward, square the aggregated grads) is provably DIFFERENT (relative
    L2 distance > 1e-2) — the implementation cannot regress to the van de Ven bug (Pitfall 2).
  - test_finite_and_nonnegative — every Fisher entry is finite and >= 0.
  - test_determinism — two same-seed calls return torch.equal tensors and equal meta.
  - test_mean_normalization — normalize=True gives global mean 1.0 within 1e-5 (fp64);
    normalizer > 0 recorded; normalized * normalizer recovers the raw estimate (D-01/D-02).
  - test_tied_tensor_dedup — the tied wte/lm_head storage appears ONCE ("wte.weight" present,
    "lm_head.weight" absent); one Fisher entry per distinct data_ptr (Pitfall 1).
  - test_rng_purity — global python/numpy/torch RNG states are bit-unchanged after the call
    (Pitfall 3: fork_rng does not cover numpy; estimate_fisher must use a local Generator).
  - test_mode_restore — the prior model.training flag is restored (train stays train, eval
    stays eval) — never an unconditional model.train().
  - test_meta_contract — fisher_meta carries the exact key set; spearman_half in [-1, 1].
"""

import random

import numpy as np
import pytest
import torch

from personacore.config import ModelConfig
from personacore.continual import estimate_fisher
from personacore.model import GPT

BLOCK_SIZE = 32
SEED = 777
N_EXAMPLES = 4

EXPECTED_META_KEYS = {
    "variant",
    "n_examples",
    "seed",
    "block_size",
    "bin_path",
    "normalized",
    "normalizer",
    "spearman_half",
    "rel_mean_change_a",
    "rel_mean_change_b",
    "spearman_method",
}


def _tiny_config() -> ModelConfig:
    # vocab_size/eos_id stay at the LOCKED defaults (8192/8184); everything else is shrunk
    # for a cheap CPU fixture (test_lora_artifact.py precedent).
    return ModelConfig(block_size=32, n_layer=1, n_head=2, n_embd=16)


@pytest.fixture()
def model():
    torch.manual_seed(1234)  # deterministic tiny weights.
    m = GPT(_tiny_config())
    m.eval()
    return m


@pytest.fixture()
def bin_path(tmp_path):
    # A few thousand random tokens < 8192 written as a flat uint16 bin (the memmap corpus shape).
    rng = np.random.default_rng(99)
    tokens = rng.integers(0, 8192, size=4096, dtype=np.uint16)
    path = tmp_path / "train.bin"
    tokens.tofile(path)
    return path


def _estimate(model, bin_path, **overrides):
    kwargs = dict(
        n_examples=N_EXAMPLES, block_size=BLOCK_SIZE, device="cpu", seed=SEED, normalize=True
    )
    kwargs.update(overrides)
    return estimate_fisher(model, bin_path, **kwargs)


def _draw_windows(bin_path, n, block_size, seed):
    """Re-derive the exact (x, y) windows estimate_fisher draws — the pinned draw pattern."""
    data = np.memmap(bin_path, dtype=np.uint16, mode="r")
    data_len = len(data)
    rng = np.random.default_rng(seed)
    windows = []
    for _ in range(n):
        start = int(rng.integers(0, data_len - block_size - 1))
        x = torch.from_numpy(data[start : start + block_size].astype(np.int64))[None]
        y = torch.from_numpy(data[start + 1 : start + 1 + block_size].astype(np.int64))[None]
        windows.append((x, y))
    return windows


def _rng_state():
    """Snapshot the full (python/numpy/torch) global RNG state (loop.py idiom)."""
    return (random.getstate(), np.random.get_state(), torch.get_rng_state())


def test_per_example_oracle(model, bin_path):
    # Brute-force per-example oracle (EWC-01): explicit batch=1 loop over the SAME windows.
    fisher, _ = _estimate(model, bin_path, normalize=False)
    named = list(model.named_parameters())
    params = [p for _, p in named]
    expected = [torch.zeros_like(p) for p in params]
    for x, y in _draw_windows(bin_path, N_EXAMPLES, BLOCK_SIZE, SEED):
        _, loss = model(x, y)
        grads = torch.autograd.grad(loss, params)
        for e, g in zip(expected, grads):
            e.add_(g.detach() ** 2)
    for (name, _), e in zip(named, expected):
        assert torch.allclose(fisher[name], e / N_EXAMPLES, rtol=1e-6, atol=0), name


def test_differs_from_batched_gradient_estimate(model, bin_path):
    # The van de Ven bug discriminator (Pitfall 2): squaring the gradient aggregated over a
    # batch of N windows is NOT the Fisher — cross-terms do not vanish. Pin the distance.
    fisher, _ = _estimate(model, bin_path, normalize=False)
    windows = _draw_windows(bin_path, N_EXAMPLES, BLOCK_SIZE, SEED)
    xb = torch.cat([x for x, _ in windows])
    yb = torch.cat([y for _, y in windows])
    named = list(model.named_parameters())
    params = [p for _, p in named]
    _, loss = model(xb, yb)
    grads = torch.autograd.grad(loss, params)
    per_example = torch.cat([fisher[name].ravel() for name, _ in named])
    batched = torch.cat([(g.detach() ** 2).ravel() for g in grads])
    rel = torch.linalg.norm(per_example - batched) / torch.linalg.norm(per_example)
    assert rel.item() > 1e-2


def test_finite_and_nonnegative(model, bin_path):
    fisher, _ = _estimate(model, bin_path)
    for name, t in fisher.items():
        assert torch.isfinite(t).all(), name
        assert (t >= 0).all(), name


def test_determinism(model, bin_path):
    # Same seed -> bit-identical tensors and equal meta (the reproducibility contract).
    f1, m1 = _estimate(model, bin_path)
    f2, m2 = _estimate(model, bin_path)
    assert f1.keys() == f2.keys()
    for name in f1:
        assert torch.equal(f1[name], f2[name]), name
    assert m1 == m2


def test_mean_normalization(model, bin_path):
    # D-01/D-02: stored Fisher is mean-normalized over ALL deduped trainable coordinates;
    # the raw estimate is recoverable via the recorded normalizer.
    fisher_n, meta_n = _estimate(model, bin_path, normalize=True)
    fisher_r, meta_r = _estimate(model, bin_path, normalize=False)
    flat = np.concatenate([t.numpy().astype(np.float64).ravel() for t in fisher_n.values()])
    assert abs(flat.mean() - 1.0) < 1e-5
    assert meta_n["normalizer"] > 0
    assert meta_n["normalizer"] == meta_r["normalizer"]  # raw mean recorded either way.
    assert meta_n["normalized"] is True and meta_r["normalized"] is False
    for name in fisher_n:
        assert torch.allclose(
            fisher_n[name] * meta_n["normalizer"], fisher_r[name], rtol=1e-6, atol=1e-30
        ), name


def test_tied_tensor_dedup(model, bin_path):
    # Pitfall 1: the tied wte/lm_head tensor must appear exactly ONCE (named_parameters
    # dedup) — one Fisher entry per distinct parameter storage.
    fisher, _ = _estimate(model, bin_path)
    assert "lm_head.weight" not in fisher
    assert "wte.weight" in fisher
    assert len(fisher) == len({p.data_ptr() for p in model.parameters()})


def test_rng_purity(model, bin_path):
    # Pitfall 3: estimate_fisher must never touch global RNG — a local np Generator draws
    # the windows and the eval-mode forward consumes no torch RNG.
    random.seed(31)
    np.random.seed(41)
    torch.manual_seed(51)
    before = _rng_state()
    _estimate(model, bin_path)
    after = _rng_state()
    assert before[0] == after[0]
    # numpy state is a tuple with an array inside — compare element-wise.
    b_np, a_np = before[1], after[1]
    assert b_np[0] == a_np[0]
    assert np.array_equal(b_np[1], a_np[1])
    assert b_np[2:] == a_np[2:]
    assert torch.equal(before[2], after[2])


def test_mode_restore(model, bin_path):
    # The PRIOR model.training flag is restored — never an unconditional model.train().
    model.train()
    _estimate(model, bin_path)
    assert model.training is True
    model.eval()
    _estimate(model, bin_path)
    assert model.training is False


def test_meta_contract(model, bin_path):
    _, meta = _estimate(model, bin_path)
    assert set(meta.keys()) == EXPECTED_META_KEYS
    assert isinstance(meta["spearman_half"], float)
    assert -1.0 <= meta["spearman_half"] <= 1.0
    assert meta["n_examples"] == N_EXAMPLES
    assert meta["seed"] == SEED
    assert meta["block_size"] == BLOCK_SIZE
    assert meta["bin_path"] == str(bin_path)
