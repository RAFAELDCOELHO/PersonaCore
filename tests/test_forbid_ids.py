"""CR-01 / DEMO-01 regression tests: the forbid_ids dead-id logits mask.

CPU-only, GPU/MPS-free, gradio-free. The flagship demo samples over the model's full
8192-id table while the frozen production tokenizer decodes only 547 live ids (256 bytes +
283 learned merges + 8 specials) — a sampled dead id crashes ``BPETokenizer.decode``
(strict ``ValueError("unknown token id: ...")``) mid-stream. The locked fix masks the
undecodable ids to ``-inf`` BEFORE the greedy argmax and BEFORE the temperature/top-k/top-p
pipeline, via the optional ``forbid_ids`` mask threaded through ``next_token``/``generate``.

The do-not-catch-ValueError contract is pinned here too: WITHOUT the mask, ``generate_text``
must fail LOUDLY with the unknown-id ValueError — the wrapper keeps catching ONLY
``UnicodeDecodeError`` (partial multi-byte glyph). Catch-and-truncate would silently swallow
genuine strict-decode defects.

  - test_next_token_greedy_respects_forbid       — masked argmax shifts off the forbidden id
  - test_next_token_sampled_never_picks_forbidden — forbidden id has exactly probability zero
  - test_undecodable_ids_mask_shape_and_content  — mask True exactly off the live id set
  - test_generate_text_with_mask_streams_clean   — wrapper streams clean with the mask
  - test_generate_text_without_mask_fails_loudly — no mask -> loud ValueError, never truncation
  - test_real_artifact_crash_settings_no_crash   — real slim artifact + frozen tokenizer at the
                                                   measured crash settings (temp 1.5, top-k off)
"""

import pathlib

import pytest
import torch

from personacore.config import ModelConfig
from personacore.generation import (
    generate_text,
    generate_text_str,
    next_token,
    undecodable_ids_mask,
)
from personacore.model import GPT

# Repo-root-anchored paths (IN-07): never depend on the pytest invocation cwd.
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
REAL_SLIM = REPO_ROOT / "checkpoints" / "model_slim.pt"  # gitignored real artifact.
TOKENIZER_PATH = REPO_ROOT / "artifacts" / "tokenizer.json"  # FROZEN production artifact.


# --------------------------------------------------------------------------- #
# Fixtures / stubs (mirrors tests/test_generation_text.py — do not diverge)
# --------------------------------------------------------------------------- #


def _tiny_model():
    """A minimal CPU GPT — eos_id (15) < vocab_size (16), small block_size for cheap crops."""
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


def _force_dead_top(model, dead_id=9, live_id=3):
    """Monkeypatch model.forward so the DEAD id always has the top logit, a LIVE id second.

    Every step: ``dead_id`` gets 1e9, ``live_id`` gets 1e8, all else -1e9. Unmasked greedy
    argmax picks the dead id; with the forbid mask the argmax shifts to the live id.
    ``targets`` is accepted to honor the locked forward signature.
    """
    vocab = model.config.vocab_size

    def _forward(idx, targets=None):
        logits = torch.full((idx.size(0), idx.size(1), vocab), -1e9)
        logits[..., dead_id] = 1e9
        logits[..., live_id] = 1e8
        return logits, None

    model.forward = _forward  # type: ignore[method-assign]


class _StrictStubTokenizer:
    """Strict stub mirroring ``BPETokenizer.decode``: unknown id -> loud ValueError.

    Decodes ids 0-8 only (one char each); any other id raises exactly the bpe.py strict-decode
    error. Exposes ``.vocab`` (ids 0-8) and ``.special_tokens`` so ``undecodable_ids_mask``
    builds from the SAME object the decode test runs against.
    """

    def __init__(self):
        self.vocab = {i: bytes([i]) for i in range(9)}
        self.special_tokens = {"<|endoftext|>": 15}
        self._id_to_str = {i: chr(ord("a") + i) for i in range(9)}

    def encode(self, text, allowed_special="all"):
        return []  # empty prompt body; the generation wrapper seeds [eos_id].

    def decode(self, ids):
        parts = []
        for idx in ids:
            if idx not in self._id_to_str:
                raise ValueError(f"unknown token id: {idx}")
            parts.append(self._id_to_str[idx])
        return "".join(parts)


# --------------------------------------------------------------------------- #
# next_token-level: the mask covers BOTH branches
# --------------------------------------------------------------------------- #


def test_next_token_greedy_respects_forbid():
    # id 7 highest (9.0), id 3 second (8.0): control argmax is 7; masked argmax shifts to 3.
    logits = torch.zeros(1, 16)
    logits[0, 7] = 9.0
    logits[0, 3] = 8.0

    assert int(next_token(logits, greedy=True)) == 7  # control: no mask -> top logit wins.

    forbid = torch.zeros(1, 16, dtype=torch.bool)
    forbid[0, 7] = True
    assert int(next_token(logits, greedy=True, forbid_ids=forbid)) == 3


def test_next_token_sampled_never_picks_forbidden():
    # Overwhelming mass on id 7 — unmasked sampling would pick it essentially every draw.
    # Masked to -inf its probability is EXACTLY zero under torch.multinomial.
    logits = torch.zeros(1, 16)
    logits[0, 7] = 100.0

    forbid = torch.zeros(1, 16, dtype=torch.bool)
    forbid[0, 7] = True

    gen = torch.Generator().manual_seed(42)
    for _ in range(50):
        tok = int(next_token(logits, temperature=1.5, top_k=None, generator=gen, forbid_ids=forbid))
        assert tok != 7, "forbidden id was sampled — the mask must zero its probability"
        assert not bool(forbid[0, tok]), f"returned id {tok} is forbidden"


# --------------------------------------------------------------------------- #
# Mask construction
# --------------------------------------------------------------------------- #


def test_undecodable_ids_mask_shape_and_content():
    class _Stub:
        vocab = {i: bytes([i]) for i in range(9)}
        special_tokens = {"<|endoftext|>": 15}

    mask = undecodable_ids_mask(_Stub(), 16)
    assert mask.shape == (1, 16)
    assert mask.dtype == torch.bool
    # True exactly at the dead ids 9-14 (6 of them); live ids 0-8 and the eos special 15 stay.
    assert int(mask.sum()) == 6
    for i in range(9):
        assert not bool(mask[0, i])
    for i in range(9, 15):
        assert bool(mask[0, i])
    assert not bool(mask[0, 15]), "eos is a registered special — it must NEVER be masked"


# --------------------------------------------------------------------------- #
# Wrapper-level: mask-or-fail-loudly (the verification contract)
# --------------------------------------------------------------------------- #


def test_generate_text_with_mask_streams_clean():
    # Dead id 9 holds the top logit every step; the mask shifts the greedy argmax to live id 3,
    # so the strict decoder only ever sees decodable ids and the stream completes clean.
    model = _tiny_model()
    _force_dead_top(model, dead_id=9, live_id=3)
    tok = _StrictStubTokenizer()

    mask = undecodable_ids_mask(tok, model.config.vocab_size)
    out = "".join(generate_text(model, tok, "", max_new_tokens=5, greedy=True, forbid_ids=mask))
    assert out == "d" * 5  # the masked argmax shifted from dead 9 to live 3 ("d") every step.


def test_generate_text_without_mask_fails_loudly():
    # NO mask: the dead id reaches the strict decoder, which must raise the unknown-id
    # ValueError. This pins the do-not-catch contract — the wrapper catches ONLY
    # UnicodeDecodeError; silently truncating would swallow genuine strict-decode defects.
    model = _tiny_model()
    _force_dead_top(model, dead_id=9, live_id=3)
    tok = _StrictStubTokenizer()

    with pytest.raises(ValueError, match="unknown token id"):
        list(generate_text(model, tok, "", max_new_tokens=5, greedy=True))


# --------------------------------------------------------------------------- #
# Real-artifact smoke at the EXACT measured crash settings
# --------------------------------------------------------------------------- #


@pytest.mark.skipif(not REAL_SLIM.exists(), reason="real slim artifact not present (CI)")
def test_real_artifact_crash_settings_no_crash():
    # The measured pre-fix crash probability at these settings (temp 1.5, top-k disabled) was
    # ~29% per 400-token generation. With the mask the dead ids are unreachable.
    from personacore.checkpoint import load_slim
    from personacore.tokenizer import from_json

    ckpt = load_slim(REAL_SLIM)
    model = GPT(ModelConfig(**ckpt["model_config"]))
    model.load_state_dict(ckpt["model"])
    model.eval()
    tok = from_json(str(TOKENIZER_PATH))  # FROZEN production artifact — never retrain.

    mask = undecodable_ids_mask(tok, model.config.vocab_size)
    # 8192 total - 547 decodable (256 bytes + 283 merges + 8 specials) = 7645 dead ids.
    assert int(mask.sum()) == 7645

    gen = torch.Generator().manual_seed(1234)
    out = generate_text_str(
        model,
        tok,
        "Once upon a time, there was a little dog named Max.",
        max_new_tokens=400,
        temperature=1.5,
        top_k=None,
        forbid_ids=mask,
        generator=gen,
    )
    assert isinstance(out, str)
