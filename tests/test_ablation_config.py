"""EVAL-03 ablation-flag semantics — the two backward-compatible ``ModelConfig``
flags (``weight_tying``, ``use_pos_emb``) and their effect on the ``GPT`` arch.

CPU-only, GPU/MPS-free, no checkpoint/fixture-file I/O. Pins three things:
  1. ``test_defaults_unchanged`` — ``GPT(ModelConfig())`` reproduces today's arch
     bit-for-bit: tied ``lm_head``/``wte`` storage AND 13,891,584 params.
  2. ``test_untie`` — ``weight_tying=False`` gives a DISTINCT ``lm_head`` storage and
     +3,145,728 params (the untied head = vocab x n_embd) -> 17,037,312.
  3. ``test_no_pos`` — ``use_pos_emb=False`` -> forward runs without error and the
     dropped ``wpe`` (block_size x n_embd) removes 98,304 params -> 13,793,280.

Wave-0 RED: this file references ``ModelConfig(weight_tying=...)`` and
``ModelConfig(use_pos_emb=...)`` — fields that do NOT exist until Plan 07-02 adds
them. The assertions go GREEN only after Plan 02. The exact param counts are the
in-venv-verified literals from 07-RESEARCH.md.
"""

import torch

from personacore.config import ModelConfig
from personacore.model import GPT


def count_parameters(model) -> int:
    # Dedup by storage pointer: a tied wte/lm_head tensor maps to one key, counted once.
    seen = {}
    for p in model.parameters():
        seen[p.data_ptr()] = p.numel()
    return sum(seen.values())


def test_defaults_unchanged():
    """Defaults reproduce today's arch: tied head + 13,891,584 params."""
    model = GPT(ModelConfig())
    assert model.lm_head.weight.data_ptr() == model.wte.weight.data_ptr()
    assert count_parameters(model) == 13_891_584


def test_untie():
    """weight_tying=False -> distinct lm_head storage, +3,145,728 params."""
    model = GPT(ModelConfig(weight_tying=False))
    assert model.lm_head.weight.data_ptr() != model.wte.weight.data_ptr()
    assert count_parameters(model) == 17_037_312


def test_no_pos():
    """use_pos_emb=False -> forward runs and the dropped wpe removes 98,304 params."""
    model = GPT(ModelConfig(use_pos_emb=False))
    idx = torch.zeros((1, 4), dtype=torch.long)
    logits, _ = model(idx)
    assert logits.shape == (1, 4, ModelConfig().vocab_size)
    assert count_parameters(model) == 13_793_280
