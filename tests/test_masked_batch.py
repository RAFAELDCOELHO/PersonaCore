"""RED tests for the masked dialogue batch sampler (DATA-03 / D-01 / D-03).

``get_batch_memmap_masked`` draws aligned windows from a uint16 token ``.bin`` and a
parallel uint8 mask ``.bin``, sets ``y`` to ``-100`` wherever the +1-shifted mask is 0,
and feeds the LOCKED ``forward(idx, targets=None)`` unchanged — ``F.cross_entropy``'s
default ``ignore_index=-100`` consumes the sentinel with zero model changes.

These are hand-built exactness fixtures (Pitfall 14 — mask off-by-ones can ONLY hide
from tests that recompute the expectation): both the token/mask arrays AND the expected
final ``y`` tensor are hand-written literals, never derived in-test from the mask. The
+1 label shift must hit token AND mask slices identically so token j's mask governs the
prediction OF token j (target-space semantics, D-01).

CPU-only, GPU/MPS-free. Do NOT weaken any assertion to make these pass early.
"""

import numpy as np
import pytest
import torch

from personacore.training.data import get_batch_memmap_masked

# Real special ids from personacore.tokenizer.special.SPECIAL_TOKENS (fixture literals).
EOS = 8184  # <|endoftext|>
USER = 8185  # <|user|>
ASST = 8186  # <|assistant|>
SYS = 8187  # <|system|>

# 14 hand-written tokens: persona -> user turn -> assistant reply -> user turn ->
# assistant reply -> eos -> next document's <|system|>. len - block_size - 1 == 1 with
# block_size=12, so np.random.randint(0, 1) deterministically draws start index 0.
#          idx:   0    1    2     3    4    5     6    7    8     9   10    11   12   13
TOKENS = [SYS, 100, USER, 200, 201, ASST, 300, 301, USER, 400, ASST, 500, EOS, SYS]
# D-01 mask (token-space): first <|user|>=0; second <|user|>=1 (it closes the prior
# assistant turn); assistant reply tokens=1; eos=1; everything else 0.
MASK = [0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0]

# Expected FINAL y for start index 0, block_size 12 — HAND-WRITTEN, not computed from
# MASK (that would re-implement the code under test). y[j] predicts token j+1, so the
# -100 placement encodes the +1 target-space shift of D-01.
EXPECTED_Y = [-100, -100, -100, -100, -100, 300, 301, USER, -100, -100, 500, EOS]


def _write_bins(tmp_path, tokens, mask):
    bin_path = tmp_path / "dialog.bin"
    mask_path = tmp_path / "dialog.mask.bin"
    np.asarray(tokens, dtype=np.uint16).tofile(bin_path)
    np.asarray(mask, dtype=np.uint8).tofile(mask_path)
    return bin_path, mask_path


def test_masked_batch_exact_y(tmp_path):
    # The FINAL y tensor must match the hand-written literal exactly, including -100 at
    # the three edge tokens (first-<|user|> masked, second-<|user|> kept, eos kept).
    bin_path, mask_path = _write_bins(tmp_path, TOKENS, MASK)

    x, y = get_batch_memmap_masked(bin_path, mask_path, batch_size=1, block_size=12, device="cpu")

    assert torch.equal(x, torch.tensor([TOKENS[0:12]], dtype=torch.int64))
    assert torch.equal(y, torch.tensor([EXPECTED_Y], dtype=torch.int64))

    # The three edge tokens, pinned individually (Pitfall 14 off-by-one family):
    # y[0,1] predicts the FIRST <|user|> (token idx 2, mask 0) -> masked to -100.
    assert y[0, 1].item() == -100
    # y[0,7] predicts the SECOND <|user|> (token idx 8, mask 1) -> real id survives.
    assert y[0, 7].item() == USER
    # y[0,11] predicts eos (token idx 12, mask 1) -> real id survives.
    assert y[0, 11].item() == EOS


def test_masked_batch_shapes_dtypes(tmp_path):
    # (1, 12) int64 for both x and y — the shapes/dtypes the LOCKED forward() consumes.
    bin_path, mask_path = _write_bins(tmp_path, TOKENS, MASK)

    x, y = get_batch_memmap_masked(bin_path, mask_path, batch_size=1, block_size=12, device="cpu")

    assert x.shape == (1, 12)
    assert y.shape == (1, 12)
    assert x.dtype == torch.int64
    assert y.dtype == torch.int64


def test_mismatched_bin_lengths_raise(tmp_path):
    # Token bin one element longer than the mask bin -> the alignment invariant raises
    # (T-11-04: misaligned bins at train time must fail loudly, never skew silently).
    bin_path, mask_path = _write_bins(tmp_path, TOKENS + [100], MASK)

    with pytest.raises(ValueError):
        get_batch_memmap_masked(bin_path, mask_path, batch_size=1, block_size=12, device="cpu")
