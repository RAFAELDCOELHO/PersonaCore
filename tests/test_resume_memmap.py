"""RED resume-trajectory test on the MEMMAP data source (PRE-02 resumability).

Extends ``test_resume_curve.py::test_resume_identical_trajectory`` to the full-corpus memmap
path: instead of ``corpus_path=`` (the in-RAM doc-split fixture), drive ``train()`` through the
new ``train_bin=``/``val_bin=`` seam pointing at a tiny ``uint16`` ``.bin`` built in ``tmp_path``
from the committed TinyStories fixture. Same kill+resume structure — ``seed_everything(1234)`` ->
reference run -> run half + ``checkpoint_path`` -> KILL -> fresh ``GPT(ModelConfig())`` ->
``resume_from`` -> assert next-step loss AND a sampled param match within ``1e-6``.

CPU-only by design: cross-device bitwise determinism is NOT guaranteed on MPS (RESEARCH A5), so
this resume oracle stays on CPU; MPS is validated only by ``test_mps_smoke.py``.

RED until Task 2 adds the memmap data branch (``train_bin``/``val_bin``) to ``train()`` and the
memmap path-support branch to ``estimate_loss``. It fails RIGHT — solely on the missing kwargs.
"""

import pathlib

import numpy as np
import torch

from personacore.config import ModelConfig, RuntimeConfig, TrainConfig
from personacore.model import GPT
from personacore.seeding import seed_everything
from personacore.tokenizer import from_json
from personacore.training.loop import train

FIXTURE_PATH = pathlib.Path(__file__).parent / "fixtures" / "tinystories_fixture.txt"
TOKENIZER_PATH = "artifacts/tokenizer.json"
EOS_ID = 8184
# CPU-pinned: cross-device bitwise determinism is NOT guaranteed on MPS (RESEARCH A5), so this
# resume oracle stays on CPU regardless of the host. MPS is validated only by test_mps_smoke.py.
CPU_RUNTIME = RuntimeConfig(device="cpu")


def _build_bins(tmp_path):
    """Encode the committed fixture through the FROZEN tokenizer into a uint16 train/val .bin pair.

    Splits at the LAST ``<|endoftext|>`` document boundary so train and val are disjoint (mirrors
    the no-leakage discipline of ``load_split``); writes flat ``uint16`` ``.bin`` files in the
    nanoGPT format ``get_batch_memmap`` reads.
    """
    tok = from_json(TOKENIZER_PATH)  # FROZEN production artifact — never retrain (Pitfall 6).
    text = FIXTURE_PATH.read_text(encoding="utf-8")
    ids = tok.encode(text, allowed_special="all")  # <|endoftext|> -> atomic eos 8184.

    # Partition into per-document token lists on the eos boundary (eos kept as terminator).
    docs, cur = [], []
    for t in ids:
        cur.append(t)
        if t == EOS_ID:
            docs.append(cur)
            cur = []
    if cur and tok.decode(cur).strip():
        docs.append(cur)
    assert len(docs) >= 2

    train_ids = np.array([t for d in docs[:-1] for t in d], dtype=np.uint16)
    val_ids = np.array([t for d in docs[-1:] for t in d], dtype=np.uint16)
    train_bin = tmp_path / "train.bin"
    val_bin = tmp_path / "val.bin"
    train_ids.tofile(train_bin)
    val_ids.tofile(val_bin)
    return train_bin, val_bin


def test_resume_identical_trajectory_memmap(tmp_path):
    train_bin, val_bin = _build_bins(tmp_path)
    cfg = TrainConfig(lr=1e-2, warmup_steps=2, max_steps=6, batch_size=4)

    # --- Reference: an uninterrupted run of all max_steps on the memmap source ---
    seed_everything(1234)
    ref_model = GPT(ModelConfig())
    ref = train(
        train_config=cfg,
        runtime_config=CPU_RUNTIME,
        model=ref_model,
        train_bin=train_bin,
        val_bin=val_bin,
        return_final_loss=True,
    )
    ref_param = ref_model.wte.weight.detach().clone()

    # --- Resumed: run half, checkpoint, KILL, fresh model, resume to the end ---
    seed_everything(1234)
    half_model = GPT(ModelConfig())
    ckpt_path = tmp_path / "latest.pt"
    train(
        train_config=cfg,
        runtime_config=CPU_RUNTIME,
        model=half_model,
        train_bin=train_bin,
        val_bin=val_bin,
        max_steps_override=3,
        checkpoint_path=ckpt_path,
    )

    fresh_model = GPT(ModelConfig())
    resumed = train(
        train_config=cfg,
        runtime_config=CPU_RUNTIME,
        model=fresh_model,
        train_bin=train_bin,
        val_bin=val_bin,
        resume_from=ckpt_path,
        return_final_loss=True,
    )
    resumed_param = fresh_model.wte.weight.detach().clone()

    # Trajectory equality within 1e-6 (the checkpoint restores RNG STATE, not a re-seed).
    assert abs(float(resumed) - float(ref)) < 1e-6
    assert torch.allclose(resumed_param, ref_param, atol=1e-6)
