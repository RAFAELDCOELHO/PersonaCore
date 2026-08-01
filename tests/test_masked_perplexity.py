"""TUNE-01: ``masked_perplexity`` — THE frozen dialogue-val gate metric (hand-fixture oracle).

Every Phase-12 smoke arm is judged by this one deterministic number; a wrong denominator
would corrupt every gate verdict (T-12-04), so the oracle hand-counts the scored-target
set instead of deriving it from the implementation.

Fixture geometry (block_size=4, 13 tokens): the non-overlapping window sweep scores each
position 1..12 exactly once as a shifted target; the mask (uint8, 1:1 with tokens, SHIFTED
with the targets) selects which of those targets enter the CE sum.

    tokens: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    mask:   [0, 1, 1, 0, 1, 0, 0, 1, 1, 1,  0,  1,  0]

Scored targets = positions {1, 2, 4, 7, 8, 9, 11} -> K = 7 (hand-counted).

CPU-only, synthetic bins in tmp_path, no artifacts.
"""

import numpy as np
import pytest
import torch
import torch.nn as nn

from personacore.evaluation import masked_perplexity

VOCAB = 16
TOKENS = np.arange(13, dtype=np.uint16)
MASK = np.array([0, 1, 1, 0, 1, 0, 0, 1, 1, 1, 0, 1, 0], dtype=np.uint8)
K = 7  # hand-counted mask==1 shifted-target positions: {1, 2, 4, 7, 8, 9, 11}
BLOCK_SIZE = 4


class _UniformLogitsModel(nn.Module):
    """``forward(idx) -> (zeros logits, None)``: uniform over VOCAB => CE = ln(VOCAB)."""

    def forward(self, idx, targets=None):
        return torch.zeros(idx.shape[0], idx.shape[1], VOCAB), None


class _FixedLogitsModel(nn.Module):
    """Non-uniform input-independent logits: CE varies WITH the target id.

    Needed for the masking-selectivity test — under uniform logits every target costs the
    same ln(VOCAB), so swapping target values would never change the sum even unmasked.
    """

    def forward(self, idx, targets=None):
        row = torch.arange(VOCAB, dtype=torch.float32)
        return row.expand(idx.shape[0], idx.shape[1], VOCAB).clone(), None


def _write_bins(tmp_path, tokens=TOKENS, mask=MASK):
    bin_path = tmp_path / "dialogue_val.bin"
    mask_path = tmp_path / "dialogue_val_mask.bin"
    tokens.tofile(bin_path)
    mask.tofile(mask_path)
    return bin_path, mask_path


def test_oracle_uniform_ppl_and_exact_denominator(tmp_path):
    # Uniform logits => per-scored-token CE = ln(16) => ppl == 16 exactly; the
    # denominator is the HAND-COUNTED K, not whatever the implementation summed.
    bin_path, mask_path = _write_bins(tmp_path)
    ppl, total = masked_perplexity(
        _UniformLogitsModel(), bin_path, mask_path, BLOCK_SIZE, device="cpu"
    )
    assert ppl == pytest.approx(float(VOCAB))
    assert total == K


def test_masked_positions_contribute_nothing(tmp_path):
    # Change token values ONLY at mask==0 target positions {3, 5, 6, 10, 12}; with
    # input-independent non-uniform logits the CE sum changes iff those targets are
    # scored — so identical (ppl, total) proves they never enter the sum.
    model = _FixedLogitsModel()
    bin_path, mask_path = _write_bins(tmp_path)
    ppl_ref, total_ref = masked_perplexity(model, bin_path, mask_path, BLOCK_SIZE, device="cpu")

    mutated = TOKENS.copy()
    for pos in (3, 5, 6, 10, 12):  # every mask==0 position in 1..12
        mutated[pos] = 15
    mut_bin = tmp_path / "mutated.bin"
    mutated.tofile(mut_bin)
    ppl_mut, total_mut = masked_perplexity(model, mut_bin, mask_path, BLOCK_SIZE, device="cpu")

    assert ppl_mut == pytest.approx(ppl_ref)
    assert total_mut == total_ref == K


def test_length_mismatch_raises_naming_both_lengths(tmp_path):
    bin_path, _ = _write_bins(tmp_path)
    short_mask = tmp_path / "short_mask.bin"
    MASK[:-1].tofile(short_mask)  # 12 elements vs 13 tokens
    with pytest.raises(ValueError, match=r"13.*12"):
        masked_perplexity(_UniformLogitsModel(), bin_path, short_mask, BLOCK_SIZE, device="cpu")


def test_zero_scored_targets_raises(tmp_path):
    bin_path, _ = _write_bins(tmp_path)
    zeros_mask = tmp_path / "zeros_mask.bin"
    np.zeros(len(TOKENS), dtype=np.uint8).tofile(zeros_mask)
    with pytest.raises(ValueError):
        masked_perplexity(_UniformLogitsModel(), bin_path, zeros_mask, BLOCK_SIZE, device="cpu")


def test_forbid_ids_renormalizes_and_lowers_ppl(tmp_path):
    # Forbid ids 12..15 — never targets at scored positions (values {1,2,4,7,8,9,11}).
    # Uniform over 16 -> ppl 16 unmasked; -inf fill renormalizes over 12 ids -> ppl 12.
    bin_path, mask_path = _write_bins(tmp_path)
    forbid = torch.zeros(1, VOCAB, dtype=torch.bool)
    forbid[0, 12:] = True

    ppl_plain, total_plain = masked_perplexity(
        _UniformLogitsModel(), bin_path, mask_path, BLOCK_SIZE, device="cpu"
    )
    ppl_forbid, total_forbid = masked_perplexity(
        _UniformLogitsModel(), bin_path, mask_path, BLOCK_SIZE, device="cpu", forbid_ids=forbid
    )

    assert total_plain == total_forbid == K
    assert ppl_forbid < ppl_plain
    assert ppl_forbid == pytest.approx(12.0)
