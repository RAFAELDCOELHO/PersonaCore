"""EVAL-01 accounting tests for the deterministic full-val perplexity sweep.

CPU-only, GPU/MPS-free — every case runs on a tiny in-memory ``GPT`` fixture
(``block_size=8, vocab_size=16, eos_id=15``) plus a hand-built ``np.uint16`` token
array written to a ``tmp_path`` corpus file. NEVER loads the trained checkpoint or
the real held-out token corpus (keep the suite CPU-fast).

The accounting bugs hide in three places, each pinned here:
  1. ``test_matches_bruteforce`` — perplexity() equals an INDEPENDENT brute-force
     per-token CE reference (hand-written in the test; it never calls perplexity()).
  2. ``test_token_count`` — the auditable denominator equals ``corpus_len - n_windows``
     (each scored window loses its first token as unpredictable, D-03).
  3. ``test_partial_window`` — the final partial window IS scored; a single dangling
     trailing token (numel < 2) is skipped.

RED until Plan 07-01 Task 2 lands ``personacore.evaluation.perplexity``; GREEN after.
"""

import math

import numpy as np
import torch
import torch.nn.functional as F

from personacore.config import ModelConfig
from personacore.evaluation import perplexity
from personacore.model import GPT


def _tiny_model():
    """A minimal CPU GPT for fast perplexity tests — never a trained checkpoint."""
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


def _write_corpus(tmp_path, n_tokens, vocab_size=16, seed=1234):
    """Build a fixed-seed uint16 token array and write it to a tmp .bin.

    Returns (path, np.ndarray) so the brute-force oracle and perplexity() see the
    identical data.
    """
    rng = np.random.default_rng(seed)
    arr = rng.integers(0, vocab_size, size=n_tokens, dtype=np.uint16)
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / "corpus.bin"
    arr.astype(np.uint16).tofile(path)
    return str(path), arr


@torch.no_grad()
def _bruteforce_ppl(model, arr, block_size):
    """INDEPENDENT brute-force reference — tiles non-overlapping windows, sums CE
    with reduction='sum', and exponentiates the grand total over the exact token
    count. Must NOT call perplexity() (that would test perplexity against itself).
    """
    model.eval()
    n = len(arr)
    total_ce = 0.0
    total_tokens = 0
    for i in range(0, n - 1, block_size):
        end = min(i + block_size + 1, n)
        chunk = torch.from_numpy(arr[i:end].astype(np.int64))
        if chunk.numel() < 2:
            continue
        x = chunk[:-1].unsqueeze(0)
        y = chunk[1:].unsqueeze(0)
        logits, _ = model(x)
        ce = F.cross_entropy(
            logits.view(-1, logits.size(-1)), y.view(-1), reduction="sum"
        )
        total_ce += ce.item()
        total_tokens += y.numel()
    return math.exp(total_ce / total_tokens), total_tokens


def test_matches_bruteforce(tmp_path):
    """perplexity() == an independent brute-force per-token CE reference (atol 1e-4)."""
    model = _tiny_model()
    block_size = 8
    path, arr = _write_corpus(tmp_path, n_tokens=300, vocab_size=16)

    ppl, ntok = perplexity(model, path, block_size=block_size, device="cpu")
    ref_ppl, ref_ntok = _bruteforce_ppl(model, arr, block_size)

    assert ntok == ref_ntok
    assert abs(ppl - ref_ppl) < 1e-4


def test_token_count(tmp_path):
    """Denominator == corpus_len - n_windows (each scored window loses its first token).

    A length divisible by block_size gives a clean window count; each window that
    holds >= 2 tokens contributes (len - 1) and thus loses exactly one token.
    """
    model = _tiny_model()
    block_size = 8
    n_tokens = 320  # 320 = 40 * 8 — divides evenly
    path, arr = _write_corpus(tmp_path, n_tokens=n_tokens, vocab_size=16)

    # Independently count the scored windows (>= 2 tokens) the sweep will produce.
    n_windows = 0
    for i in range(0, n_tokens - 1, block_size):
        end = min(i + block_size + 1, n_tokens)
        if end - i >= 2:
            n_windows += 1

    _, ntok = perplexity(model, path, block_size=block_size, device="cpu")
    assert ntok == n_tokens - n_windows


def test_partial_window(tmp_path):
    """The final partial window is scored; a single dangling trailing token is skipped."""
    model = _tiny_model()
    block_size = 8

    # (a) Length that does NOT divide evenly -> the final partial window contributes
    #     (len(chunk) - 1) transitions and IS scored.
    n_partial = 21  # 21 = 2*8 + 5 -> a final window of 5 tokens (4 transitions)
    path_p, arr_p = _write_corpus(tmp_path / "p", n_tokens=n_partial, vocab_size=16, seed=7)
    ppl_p, ntok_p = perplexity(model, path_p, block_size=block_size, device="cpu")
    ref_ppl_p, ref_ntok_p = _bruteforce_ppl(model, arr_p, block_size)
    assert ntok_p == ref_ntok_p
    assert abs(ppl_p - ref_ppl_p) < 1e-4

    # (b) A length leaving exactly one dangling token confirms it is skipped: the
    #     start at i = 2*block_size yields a window slice [16:17] of numel 1 -> continue.
    n_dangle = 17  # windows start at 0, 8, 16; the i=16 window slice is [16:17] (1 token)
    path_d, arr_d = _write_corpus(tmp_path / "d", n_tokens=n_dangle, vocab_size=16, seed=9)
    _, ntok_d = perplexity(model, path_d, block_size=block_size, device="cpu")
    # Scored windows: [0:9] (8 transitions) + [8:17] (8 transitions) = 16; the [16:17]
    # dangling single token is skipped (numel < 2).
    assert ntok_d == 16
