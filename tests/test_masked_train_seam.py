"""train_mask_bin / val_mask_bin loop-seam tests (Phase 12, TUNE-01 / DEBT precedent).

The Stage-2 fine-tune needs the memmap data branch to draw MASKED batches — user-turn
targets carry ``-100`` (``F.cross_entropy``'s ignore_index) so the loss scores assistant
tokens only. The seam must be ADDITIVE in the penalty_fn register: two default-None kwargs
(``train_mask_bin``, ``val_mask_bin``) on ``train()``; when both are None the v1.0
trajectory is reproduced bit-for-bit (the in-process identity idiom from
tests/test_loop_penalty_fn.py).

``val_mask_bin`` routes ``estimate_loss``'s val draws through ``get_batch_memmap_masked``
INSIDE the existing ``_rng_state()``/``_restore_rng`` snapshot — the resume-equality
contract (TRAIN-04) must survive the masked path unchanged. CPU-only, synthetic bins.
"""

import hashlib
import pathlib

import numpy as np
import pytest
import torch

import personacore.training.loop as loop_mod
from personacore.config import ModelConfig, RuntimeConfig, TrainConfig
from personacore.model import BigramLanguageModel
from personacore.seeding import seed_everything
from personacore.training.loop import estimate_loss, train

CORPUS_PATH = pathlib.Path(__file__).parent / "fixtures" / "bigram_corpus.txt"
EOS_ID = 8184

VOCAB = 16
BLOCK = 8


def _tiny_bins(tmp_path, stem="train"):
    """Aligned uint16 token bin + uint8 mask bin (the test_retention_ppl tofile recipe).

    64 tokens; the mask's period-8 half-zero pattern guarantees EVERY block_size=8 window
    contains mask==0 positions, so -100 sentinels must appear in every drawn target.
    """
    ids = np.array(list(range(VOCAB)) * 4, dtype=np.uint16)
    mask = np.array(([0] * 4 + [1] * 4) * 8, dtype=np.uint8)
    assert len(ids) == len(mask)
    bin_path = tmp_path / f"{stem}.bin"
    ids.tofile(bin_path)
    mask_path = tmp_path / f"{stem}_mask.bin"
    mask.tofile(mask_path)
    return bin_path, mask_path


def test_train_mask_bin_routes_through_masked_draw(tmp_path, monkeypatch):
    # Routing: with train_mask_bin set, batch_fn draws via get_batch_memmap_masked and the
    # -100 sentinels (user-turn masking) reach the targets on every drawn batch.
    bin_path, mask_path = _tiny_bins(tmp_path)
    real = loop_mod.get_batch_memmap_masked
    captured = []

    def spy(*args, **kwargs):
        x, y = real(*args, **kwargs)
        captured.append(y)
        return x, y

    monkeypatch.setattr(loop_mod, "get_batch_memmap_masked", spy)
    train(
        train_config=TrainConfig(max_steps=2, warmup_steps=0, batch_size=2),
        runtime_config=RuntimeConfig(device="cpu"),
        model_config=ModelConfig(vocab_size=VOCAB, block_size=BLOCK),
        train_bin=bin_path,
        train_mask_bin=mask_path,
    )
    assert captured, "train_mask_bin set but get_batch_memmap_masked was never called"
    assert all((y == -100).any() for y in captured)


def test_train_mask_bin_without_train_bin_raises(tmp_path):
    # Guard: a mask without its token bin is a config error — fail loud, name both kwargs.
    _, mask_path = _tiny_bins(tmp_path)
    with pytest.raises(ValueError, match=r"train_mask_bin.*train_bin"):
        train(
            train_config=TrainConfig(max_steps=1, warmup_steps=0, batch_size=2),
            runtime_config=RuntimeConfig(device="cpu"),
            model_config=ModelConfig(vocab_size=VOCAB, block_size=BLOCK),
            train_mask_bin=mask_path,
        )


def test_val_mask_bin_routes_val_draws(tmp_path, monkeypatch):
    # Capture-count idiom: with val_mask_bin set, EVERY estimate_loss val draw routes through
    # get_batch_memmap_masked(val_bin, val_mask_bin, ...) — iters=20 draws per eval event.
    train_bin, train_mask = _tiny_bins(tmp_path, "train")
    val_bin, val_mask = _tiny_bins(tmp_path, "val")
    real = loop_mod.get_batch_memmap_masked
    calls = []

    def spy(bin_path, mask_path, *args, **kwargs):
        calls.append((pathlib.Path(bin_path), pathlib.Path(mask_path)))
        return real(bin_path, mask_path, *args, **kwargs)

    monkeypatch.setattr(loop_mod, "get_batch_memmap_masked", spy)
    train(
        train_config=TrainConfig(max_steps=1, warmup_steps=0, batch_size=2),
        runtime_config=RuntimeConfig(device="cpu"),
        model_config=ModelConfig(vocab_size=VOCAB, block_size=BLOCK),
        train_bin=train_bin,
        train_mask_bin=train_mask,
        val_bin=val_bin,
        val_mask_bin=val_mask,
        log_path=tmp_path / "run.csv",
        eval_interval=1,
    )
    val_calls = [c for c in calls if c == (val_bin, val_mask)]
    assert len(val_calls) == 20  # estimate_loss default iters=20, one eval event
    assert any(c == (train_bin, train_mask) for c in calls)  # train draws masked too


def test_estimate_loss_masked_draw_inside_rng_snapshot(tmp_path):
    # The _rng_state()/_restore_rng wrapper still encloses the masked val draw: the global
    # RNG streams are bit-identical before and after (the resume-equality contract).
    val_bin, val_mask = _tiny_bins(tmp_path, "val")
    seed_everything(7)
    model = BigramLanguageModel(vocab_size=VOCAB)
    torch_before = torch.get_rng_state().clone()
    np_before = np.random.get_state()
    loss = estimate_loss(
        model,
        val_bin,
        TrainConfig(batch_size=2),
        ModelConfig(vocab_size=VOCAB, block_size=BLOCK),
        "cpu",
        iters=3,
        mask_bin=val_mask,
    )
    assert np.isfinite(loss)
    assert torch.equal(torch.get_rng_state(), torch_before)
    np_after = np.random.get_state()
    assert np_before[0] == np_after[0]
    assert (np_before[1] == np_after[1]).all()
    assert np_before[2:] == np_after[2:]


# ---- default-None v1.0 identity (the test_loop_penalty_fn._run_recipe idiom, verbatim) ----


def _param_sha256(model):
    """sha256 of the bigram's single parameter tensor — the bitwise trajectory fingerprint."""
    weight = model.token_embedding_table.weight
    return hashlib.sha256(weight.detach().cpu().contiguous().numpy().tobytes()).hexdigest()


def _run_recipe(log_path, **train_kwargs):
    """Run the golden fixture's exact meta recipe; return (csv_text, final_loss_repr, sha256)."""
    cfg = TrainConfig(lr=1e-2, warmup_steps=2, max_steps=5, batch_size=4)
    seed_everything(1234)
    model = BigramLanguageModel(vocab_size=ModelConfig().vocab_size)
    final = train(
        train_config=cfg,
        runtime_config=RuntimeConfig(device="cpu"),
        model=model,
        corpus_path=CORPUS_PATH,
        eos_id=EOS_ID,
        log_path=log_path,
        eval_interval=1,
        return_final_loss=True,
        **train_kwargs,
    )
    return pathlib.Path(log_path).read_text(), repr(float(final)), _param_sha256(model)


def test_omitted_equals_explicit_none_identity(tmp_path):
    # Platform-independent v1.0-identity: kwargs omitted vs train_mask_bin=None,
    # val_mask_bin=None must be bitwise identical (CSV text, final-loss repr, param sha256).
    omitted = _run_recipe(tmp_path / "omitted.csv")
    explicit_none = _run_recipe(
        tmp_path / "none.csv", train_mask_bin=None, val_mask_bin=None
    )
    assert omitted == explicit_none
