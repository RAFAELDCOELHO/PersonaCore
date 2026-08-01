"""DEBT-02: retention PPL applies the dead-id ``forbid_ids`` mask, frozen one way.

A uniform-logits stub makes the effect exactly computable: with vocab ``V`` and ``K``
dead ids, unmasked PPL is ``V`` (uniform softmax) and masked PPL is ``V - K`` (the
``-inf`` fill redistributes all mass onto decodable ids). The two MUST differ — that is
the observable case where probability mass sits on dead ids.

``retention_perplexity`` is THE function for every forgetting-curve point (Phase 12/13);
the unmasked ``perplexity`` remains the v1.0 headline semantics (2.1066 reproduction).
CPU-only, synthetic bin, no artifacts.
"""

import numpy as np
import pytest
import torch
import torch.nn as nn

from personacore.evaluation import perplexity, retention_perplexity
from personacore.generation.text import undecodable_ids_mask

VOCAB = 16
LIVE_IDS = set(range(10)) | {10}  # 10 vocab ids + 1 special (eos) = 11 decodable
DEAD_COUNT = VOCAB - len(LIVE_IDS)  # 5 dead ids


class _UniformLogitsModel(nn.Module):
    """``forward(idx) -> (zeros logits, None)``: uniform distribution over VOCAB."""

    def forward(self, idx, targets=None):
        return torch.zeros(idx.shape[0], idx.shape[1], VOCAB), None


class _StubTokenizer:
    """Duck-typed for ``undecodable_ids_mask``: ids 0..9 in vocab, id 10 the special."""

    vocab = {i: bytes([65 + i]) for i in range(10)}
    special_tokens = {"<|endoftext|>": 10}


@pytest.fixture()
def val_bin(tmp_path):
    ids = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10] * 3, dtype=np.uint16)
    path = tmp_path / "val.bin"
    ids.tofile(path)
    return path


def test_masked_ppl_differs_from_unmasked_when_mass_on_dead_ids(val_bin):
    model = _UniformLogitsModel()
    mask = undecodable_ids_mask(_StubTokenizer(), VOCAB)

    ppl_unmasked, n = perplexity(model, val_bin, block_size=8, device="cpu")
    ppl_masked, n_masked = perplexity(model, val_bin, block_size=8, device="cpu", forbid_ids=mask)

    assert n == n_masked  # same auditable denominator either way
    assert ppl_unmasked == pytest.approx(VOCAB)  # uniform over 16 ids
    assert ppl_masked == pytest.approx(VOCAB - DEAD_COUNT)  # mass redistributed to 11 live ids
    assert ppl_masked != pytest.approx(ppl_unmasked)


def test_retention_perplexity_is_the_masked_path(val_bin):
    model = _UniformLogitsModel()
    tok = _StubTokenizer()

    ppl_retention, n = retention_perplexity(
        model, val_bin, block_size=8, device="cpu", tokenizer=tok
    )

    mask = undecodable_ids_mask(tok, VOCAB)
    ppl_direct, _ = perplexity(model, val_bin, block_size=8, device="cpu", forbid_ids=mask)
    assert ppl_retention == pytest.approx(ppl_direct)
    assert ppl_retention == pytest.approx(VOCAB - DEAD_COUNT)
    assert n > 0
