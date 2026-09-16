"""Plan 27-02: the ``on_draw`` capture point on the masked loader, threaded through ``train()``.

RELRN-04's data-order proof is a sha256 over the sampler's offset stream (D-26 iii). The sampler
draws from the GLOBAL NumPy RNG, so ``get_batch_memmap_masked(..., on_draw=...)`` is the only
byte-neutral place that stream is observable (D-29), and ``train()`` threads it to both TRAINING
draws (D-30). These tests pin that the default path is unchanged, that a recorder sees every
teaching AND replay draw in call order, that the digest is a function of seed and bins, and that a
resume chain reproduces one uninterrupted run's stream and adapter tensors: RESEARCH assumption
A1, which plan 27-03's rung ladder rests on.

Tiny random-init GPT (2 layers, D-31), CPU only, and no ``log_path`` anywhere (see ``_run``).
"""

import collections
import hashlib
import inspect
import pathlib

import numpy as np
import pytest
import torch

import personacore.training.data as data_mod
import personacore.training.loop as loop_mod
from personacore.config import ModelConfig, RuntimeConfig, TrainConfig
from personacore.lora import LoRAConfig, inject_lora, lora_state_dict, mark_only_lora_trainable
from personacore.model import GPT
from personacore.seeding import seed_everything
from personacore.training.loop import train

_BLOCK = 32
_BATCH = 2
_REPLAY_WINDOWS = 3  # ceil division at batch 2: replay micro-batches of 2, then 1, per step


def _tiny_cfg():
    return ModelConfig(block_size=_BLOCK, n_layer=2, n_head=2, n_embd=16)


def _bins(root, stem, windows, *, vocab):
    """A ``uint16`` bin of ``windows * 32 + 1`` ids below ``vocab`` and its all-ones ``uint8`` mask.

    The ``tests/test_phase22_wiring.py`` ``_pair`` shape. The ids come from a LOCAL generator
    seeded by ``stem``, never from the global NumPy RNG the sampler draws from, so every tree
    holds the same bytes.
    """
    root.mkdir(parents=True, exist_ok=True)
    n = windows * _BLOCK + 1  # + 1: the shifted target
    bin_path, mask_path = root / f"{stem}.bin", root / f"{stem}_mask.bin"
    ids = np.random.default_rng(list(stem.encode())).integers(0, vocab, size=n)
    ids.astype(np.uint16).tofile(bin_path)
    np.ones(n, dtype=np.uint8).tofile(mask_path)
    return bin_path, mask_path


def _tree(root):
    """The train, replay and val bin pairs one run reads."""
    vocab = _tiny_cfg().vocab_size
    return {s: _bins(root, s, w, vocab=vocab) for s, w in (("train", 8), ("replay", 8), ("val", 2))}


def _recorder(train_bin):
    """``(callback, state)``: each draw appends ``(str(bin_path), ix as "<u8" bytes)`` to
    ``state["draws"]`` and folds those bytes plus a 1-byte tag into ``state["sha"]``.

    The tag is 0 for ``train_bin`` and 1 for any other bin, by path equality (the rule plan
    27-03's recorder uses). The path itself is never hashed, so equal-shaped arms in different
    trees hash equal.
    """
    state = {"draws": [], "sha": hashlib.sha256()}

    def callback(bin_path, ix):
        raw = ix.astype("<u8").tobytes()
        state["draws"].append((str(bin_path), raw))
        state["sha"].update(raw + (b"\x00" if str(bin_path) == str(train_bin) else b"\x01"))

    return callback, state


def _named(draws):
    """``draws`` without the tree-specific directory: ``(bin file name, bytes)`` per draw."""
    return [(pathlib.PurePath(path).name, raw) for path, raw in draws]


def _run(
    tree, *, seed, steps, on_draw, resume_from=None, max_steps_override=None, checkpoint_path=None
):
    """Train an injected tiny GPT through the real ``train()`` on ``tree``'s bins; return it.

    PRECONDITION: no ``log_path``, deliberately. Without it ``csv is None`` inside ``train()``,
    so the eval branch never calls ``estimate_loss``: the third loader call site, un-threaded
    and RNG-neutral, never runs, and every loader call is a draw a training step consumed.

    A fresh run is seeded right before its model is built. A resumed run is not: the checkpoint
    restores the RNG state.
    """
    if resume_from is None:
        seed_everything(seed)
    cfg = _tiny_cfg()
    model = GPT(cfg)
    inject_lora(model, LoRAConfig(r=4))
    mark_only_lora_trainable(model)
    train(
        train_config=TrainConfig(
            lr=1e-3, batch_size=_BATCH, max_steps=steps, warmup_steps=1, weight_decay=0.0, seed=seed
        ),
        runtime_config=RuntimeConfig(device="cpu"),
        model=model,
        model_config=cfg,
        train_bin=tree["train"][0],
        train_mask_bin=tree["train"][1],
        val_bin=tree["val"][0],
        val_mask_bin=tree["val"][1],
        replay_bin=tree["replay"][0],
        replay_mask_bin=tree["replay"][1],
        replay_windows=_REPLAY_WINDOWS,
        eval_interval=steps,
        checkpoint_interval=1,
        on_draw=on_draw,
        resume_from=resume_from,
        max_steps_override=max_steps_override,
        checkpoint_path=checkpoint_path,
    )
    return model


def test_on_draw_none_is_byte_neutral(tmp_path):
    """D-29: under one seed the loader returns identical tensors with no kwarg, ``None`` or a
    recorder, and the recorder holds exactly the offsets a bare ``np.random.randint`` draws."""
    bin_path, mask_path = _bins(tmp_path, "train", 8, vocab=_tiny_cfg().vocab_size)
    cb, state = _recorder(bin_path)
    draw = data_mod.get_batch_memmap_masked

    np.random.seed(7)
    x0, y0 = draw(bin_path, mask_path, 4, _BLOCK, "cpu")
    np.random.seed(7)
    x1, y1 = draw(bin_path, mask_path, 4, _BLOCK, "cpu", on_draw=None)
    np.random.seed(7)
    x2, y2 = draw(bin_path, mask_path, 4, _BLOCK, "cpu", on_draw=cb)
    np.random.seed(7)
    ix_ref = np.random.randint(0, len(np.fromfile(bin_path, dtype=np.uint16)) - _BLOCK - 1, size=4)

    assert torch.equal(x0, x1) and torch.equal(x0, x2)
    assert torch.equal(y0, y1) and torch.equal(y0, y2)
    assert [path for path, _ in state["draws"]] == [str(bin_path)]
    assert np.frombuffer(state["draws"][0][1], dtype="<u8").tolist() == ix_ref.tolist()


def test_offset_stream_hash_covers_every_draw(tmp_path, monkeypatch):
    """D-30: the recorder sees EVERY loader draw a training step consumes, in call order, with its
    bin: per step, the teaching draw of ``batch_size`` 2 and then replay micro-batches of 2 and 1.

    The 6-call count holds because ``_run`` passes NO ``log_path``, so ``csv is None`` and
    ``estimate_loss`` never runs. With a ``log_path``, the eval at step 2 would add one
    ``estimate_loss`` call, i.e. 20 val-bin loader calls at its default ``iters``, which the
    recorder deliberately does not see. The spy asserts no val-bin call happened, so that
    precondition is measured here rather than assumed.
    """
    calls = []

    def spy(bin_path, mask_path, batch_size, *args, **kwargs):
        calls.append((bin_path, batch_size))
        return data_mod.get_batch_memmap_masked(bin_path, mask_path, batch_size, *args, **kwargs)

    monkeypatch.setattr(loop_mod, "get_batch_memmap_masked", spy)
    tree = _tree(tmp_path)
    train_bin, replay_bin, val_bin = (tree[stem][0] for stem in ("train", "replay", "val"))
    cb, state = _recorder(train_bin)
    _run(tree, seed=11, steps=2, on_draw=cb)

    assert calls == [(train_bin, 2), (replay_bin, 2), (replay_bin, 1)] * 2
    assert all(path != val_bin for path, _ in calls)
    recorded = [path for path, _ in state["draws"]]
    expected = [str(path) for path, _ in calls]
    unseen = collections.Counter(expected) - collections.Counter(recorded)
    assert recorded == expected, (
        f"the recorder saw {len(recorded)} of the {len(expected)} loader draws; "
        f"unseen per bin: {dict(unseen)}"
    )
    assert [len(raw) for _, raw in state["draws"]] == [8 * n for _, n in calls]
    assert sum(len(raw) for _, raw in state["draws"]) == 8 * sum(n for _, n in calls)


def test_offset_stream_differs_by_seed_and_equals_by_seed(tmp_path):
    """D-26 (iii): the digest is a function of seed and bins. Equal seeds in two fresh trees hash
    equal, draw for draw; a different seed hashes different."""
    streams = {}
    for name, seed in (("a", 11), ("b", 11), ("c", 12)):
        tree = _tree(tmp_path / name)
        cb, streams[name] = _recorder(tree["train"][0])
        _run(tree, seed=seed, steps=2, on_draw=cb)

    assert [len(streams[name]["draws"]) for name in "abc"] == [6, 6, 6]
    assert streams["a"]["sha"].hexdigest() == streams["b"]["sha"].hexdigest()
    assert streams["a"]["sha"].hexdigest() != streams["c"]["sha"].hexdigest()
    assert _named(streams["a"]["draws"]) == _named(streams["b"]["draws"])


def test_rung_chain_stream_equals_one_run(tmp_path):
    """RESEARCH A1, measured: a resume chain (1 step, then resume to 2) reproduces an
    uninterrupted 2-step run's offset stream AND its adapter tensors bit for bit, replay included.

    ONE recorder spans the chain, so its stream is B1's draws followed by B2's. Before the resume
    the global RNG is re-seeded, as a restarted process would be, so the stream can only match
    if the checkpoint's saved NumPy state wins.
    """
    one = _tree(tmp_path / "one")
    cb_a, a = _recorder(one["train"][0])
    model_a = _run(one, seed=11, steps=2, on_draw=cb_a)

    chain = _tree(tmp_path / "chain")
    ckpt = tmp_path / "chain" / "latest.pt"
    cb_b, b = _recorder(chain["train"][0])
    _run(chain, seed=11, steps=2, on_draw=cb_b, max_steps_override=1, checkpoint_path=ckpt)
    assert len(b["draws"]) == 3  # the first link stopped after one step
    seed_everything(11)
    model_b = _run(
        chain,
        seed=11,
        steps=2,
        on_draw=cb_b,
        resume_from=ckpt,
        max_steps_override=2,
        checkpoint_path=ckpt,
    )

    assert len(a["draws"]) == 6
    assert b["sha"].hexdigest() == a["sha"].hexdigest()
    assert _named(b["draws"]) == _named(a["draws"])
    adapter_a, adapter_b = lora_state_dict(model_a), lora_state_dict(model_b)
    assert adapter_a and adapter_a.keys() == adapter_b.keys()
    for key in adapter_a:
        assert torch.equal(adapter_a[key], adapter_b[key]), key


def test_train_accepts_on_draw_as_keyword_only_none(tmp_path):
    """The signature pins, and a non-callable ``on_draw`` raises at the first draw instead of
    being swallowed."""
    for fn in (train, data_mod.get_batch_memmap_masked):
        param = inspect.signature(fn).parameters["on_draw"]
        assert param.kind is inspect.Parameter.KEYWORD_ONLY and param.default is None, fn.__name__

    with pytest.raises(TypeError, match="not callable"):
        _run(_tree(tmp_path), seed=11, steps=2, on_draw=object())
