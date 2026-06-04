"""RED resume-trajectory + curve-reproducibility tests for the loop (TRAIN-04 / TRAIN-06).

Modeled on ``test_checkpoint.py::test_resume_identical_trajectory`` (lines 43-80): a killed-and-
resumed run must continue the SAME trajectory as an uninterrupted one — next-step loss AND a
sampled param match within 1e-6 — now on the real ``BigramLanguageModel`` + ``build_scheduler``
instead of the toy Linear. The CSV log must also survive the restart: concatenating the pre-kill
and post-resume rows equals an uninterrupted run's rows, with the header written exactly once
(Pitfall 4 — Kaggle session restarts).

RED until Plan 02 implements ``personacore.training.{loop,schedule,data}``. CPU-only, GPU-free.
"""

import csv
import pathlib

import torch

from personacore.config import ModelConfig, TrainConfig
from personacore.model import BigramLanguageModel
from personacore.seeding import seed_everything
from personacore.training.loop import train

CORPUS_PATH = pathlib.Path(__file__).parent / "fixtures" / "bigram_corpus.txt"
EOS_ID = 8184


def _read_rows(path):
    with open(path, newline="") as f:
        return list(csv.reader(f))


def _build():
    # The real bigram instead of the toy Linear used in test_checkpoint.py:_build.
    model = BigramLanguageModel(vocab_size=ModelConfig().vocab_size)
    return model


def test_resume_identical_trajectory(tmp_path):
    cfg = TrainConfig(lr=1e-2, warmup_steps=2, max_steps=6, batch_size=4)

    # --- Reference: an uninterrupted run of all max_steps ---
    seed_everything(1234)
    ref_model = _build()
    ref = train(
        train_config=cfg,
        model=ref_model,
        corpus_path=CORPUS_PATH,
        eos_id=EOS_ID,
        return_final_loss=True,
    )
    ref_param = ref_model.token_embedding_table.weight.detach().clone()

    # --- Resumed: run half, checkpoint, KILL, fresh model, resume to the end ---
    seed_everything(1234)
    half_model = _build()
    ckpt_path = tmp_path / "latest.pt"
    train(
        train_config=cfg,
        model=half_model,
        corpus_path=CORPUS_PATH,
        eos_id=EOS_ID,
        max_steps_override=3,
        checkpoint_path=ckpt_path,
    )

    fresh_model = _build()
    resumed = train(
        train_config=cfg,
        model=fresh_model,
        corpus_path=CORPUS_PATH,
        eos_id=EOS_ID,
        resume_from=ckpt_path,
        return_final_loss=True,
    )
    resumed_param = fresh_model.token_embedding_table.weight.detach().clone()

    # Trajectory equality within 1e-6 (the checkpoint restores RNG STATE, not a re-seed).
    assert abs(float(resumed) - float(ref)) < 1e-6
    assert torch.allclose(resumed_param, ref_param, atol=1e-6)


def test_csv_curve_survives_restart(tmp_path):
    cfg = TrainConfig(lr=1e-2, warmup_steps=2, max_steps=6, batch_size=4)

    # Uninterrupted reference curve.
    seed_everything(1234)
    ref_log = tmp_path / "ref.csv"
    train(
        train_config=cfg,
        model=_build(),
        corpus_path=CORPUS_PATH,
        eos_id=EOS_ID,
        log_path=ref_log,
    )
    ref_rows = _read_rows(ref_log)

    # Killed-and-resumed run writing to the SAME csv path across the restart.
    seed_everything(1234)
    split_log = tmp_path / "split.csv"
    ckpt_path = tmp_path / "latest.pt"
    train(
        train_config=cfg,
        model=_build(),
        corpus_path=CORPUS_PATH,
        eos_id=EOS_ID,
        max_steps_override=3,
        checkpoint_path=ckpt_path,
        log_path=split_log,
    )
    train(
        train_config=cfg,
        model=_build(),
        corpus_path=CORPUS_PATH,
        eos_id=EOS_ID,
        resume_from=ckpt_path,
        log_path=split_log,
    )
    split_rows = _read_rows(split_log)

    # Header appears exactly once across the restart (Pitfall 4), and the concatenated curve
    # equals the uninterrupted one row-for-row.
    header = ref_rows[0]
    assert split_rows.count(header) == 1
    assert split_rows == ref_rows


class _StatefulFakeScaler:
    """A GradScaler-shaped stand-in whose ``_scale`` evolves each step, with (de)serializable state.

    On CPU the real ``GradScaler`` is a no-op (``enabled=runtime.amp`` is False), so its scale
    factor never moves and a missing-serialization bug is invisible. This fake makes the evolving
    scaler state observable on a CPU box: it grows ``_scale`` every optimizer step and exposes
    ``state_dict``/``load_state_dict`` so a CPU test can prove the loop checkpoints AND restores
    that state across a kill+resume — the fp16/P100 contract (TRAIN-04 / CR-01) the real scaler
    would otherwise only exercise on a GPU.
    """

    def __init__(self, init_scale=2.0):
        self._scale = float(init_scale)
        self.restored_from = None

    def scale(self, loss):
        return loss  # a real tensor so .backward() works

    def unscale_(self, optimizer):
        pass

    def step(self, optimizer):
        optimizer.step()

    def update(self):
        self._scale *= 2.0  # "grow" like a real scaler so the value is non-default after steps

    def state_dict(self):
        return {"scale": self._scale}

    def load_state_dict(self, sd):
        self._scale = sd["scale"]
        self.restored_from = sd["scale"]


def test_scaler_state_checkpointed_and_restored(tmp_path):
    # CR-01 / TRAIN-04: the GradScaler's evolving scale factor MUST survive a kill+resume, or the
    # fp16/P100 path restarts from the default scale and diverges. CPU can't see this with the
    # real (disabled) scaler, so we inject a stateful fake and assert save+restore of its state.
    cfg = TrainConfig(lr=1e-2, warmup_steps=0, max_steps=4, batch_size=4)
    ckpt_path = tmp_path / "latest.pt"

    seed_everything(1234)
    s1 = _StatefulFakeScaler(init_scale=2.0)
    train(
        train_config=cfg,
        model=_build(),
        corpus_path=CORPUS_PATH,
        eos_id=EOS_ID,
        scaler=s1,
        max_steps_override=2,
        checkpoint_path=ckpt_path,
    )
    saved_scale = s1._scale
    assert saved_scale != 2.0  # the scaler evolved over the run

    blob = torch.load(ckpt_path, weights_only=False)
    assert blob["scaler"] == {"scale": saved_scale}  # SAVE serializes the scaler state

    # Resume into a fresh scaler sitting at the default — it MUST be restored to the saved value,
    # not left at the default (exactly the gap CR-01 describes).
    s2 = _StatefulFakeScaler(init_scale=2.0)
    train(
        train_config=cfg,
        model=_build(),
        corpus_path=CORPUS_PATH,
        eos_id=EOS_ID,
        scaler=s2,
        resume_from=ckpt_path,
        max_steps_override=4,
        checkpoint_path=ckpt_path,
    )
    assert s2.restored_from == saved_scale  # LOAD restored the evolved scale, not the default


def test_resume_from_pre_scaler_checkpoint_is_backward_compatible(tmp_path):
    # A legacy checkpoint written before scaler serialization has NO "scaler" key. Resuming must
    # not crash and must skip the scaler restore (open-dict forward/backward compatibility).
    cfg = TrainConfig(lr=1e-2, warmup_steps=0, max_steps=4, batch_size=4)
    ckpt_path = tmp_path / "latest.pt"

    seed_everything(1234)
    train(
        train_config=cfg,
        model=_build(),
        corpus_path=CORPUS_PATH,
        eos_id=EOS_ID,
        max_steps_override=2,
        checkpoint_path=ckpt_path,
    )
    # Simulate a pre-fix checkpoint by stripping the scaler key entirely.
    blob = torch.load(ckpt_path, weights_only=False)
    blob.pop("scaler", None)
    torch.save(blob, ckpt_path)

    s = _StatefulFakeScaler(init_scale=2.0)
    train(
        train_config=cfg,
        model=_build(),
        corpus_path=CORPUS_PATH,
        eos_id=EOS_ID,
        scaler=s,
        resume_from=ckpt_path,
        max_steps_override=4,
        checkpoint_path=ckpt_path,
    )
    assert s.restored_from is None  # nothing restored from a legacy (scaler-less) checkpoint
