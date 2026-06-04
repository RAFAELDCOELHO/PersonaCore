"""Checkpoint unit tests (ENV-04 / QA-02): kill-and-resume trajectory equality,
open-dict extensibility, and git-SHA provenance.

The critical test (test_resume_identical_trajectory) proves the checkpoint restores
generator STATE (not a re-seed): a killed-and-resumed run must continue the SAME
trajectory as an uninterrupted one, bit-identical within 1e-6. All CPU-only.
"""

import subprocess

import torch

from personacore.checkpoint import CKPT_SCHEMA_VERSION, load_checkpoint, save_checkpoint
from personacore.config import ModelConfig, TrainConfig
from personacore.provenance import git_sha
from personacore.seeding import seed_everything


def _build():
    """A toy nn.Linear + AdamW + LR scheduler stand-in for the real (Phase 3/4) model."""
    model = torch.nn.Linear(4, 1)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-2)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.99)
    return model, optimizer, scheduler


def _train_step(model, optimizer, scheduler):
    """One optimization step on randomly-drawn synthetic data.

    Data is drawn from the GLOBAL torch RNG so the per-step input depends on RNG
    STATE — this is what makes trajectory equality a real test of state restore.
    """
    x = torch.rand(8, 4)
    y = torch.rand(8, 1)
    loss = torch.nn.functional.mse_loss(model(x), y)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    scheduler.step()
    return loss.item()


def test_resume_identical_trajectory(tmp_path):
    # --- Reference: an uninterrupted run of N + 1 steps ---
    seed_everything(1234)
    ref_model, ref_opt, ref_sched = _build()
    for _ in range(5):
        _train_step(ref_model, ref_opt, ref_sched)
    ref_next_loss = _train_step(ref_model, ref_opt, ref_sched)
    ref_param = ref_model.weight.detach().clone()

    # --- Resumed run: N steps, checkpoint, KILL, fresh objects, resume, +1 step ---
    seed_everything(1234)
    model, opt, sched = _build()
    for _ in range(5):
        _train_step(model, opt, sched)

    ckpt_path = tmp_path / "latest.pt"
    save_checkpoint(
        ckpt_path,
        model=model,
        optimizer=opt,
        scheduler=sched,
        step=5,
        model_config=ModelConfig(),
        train_config=TrainConfig(),
        git_sha=git_sha(),
    )

    # "Kill" — build completely fresh objects, then resume from the checkpoint.
    fresh_model, fresh_opt, fresh_sched = _build()
    ckpt = load_checkpoint(ckpt_path, model=fresh_model, optimizer=fresh_opt, scheduler=fresh_sched)
    assert ckpt["step"] == 5

    resumed_next_loss = _train_step(fresh_model, fresh_opt, fresh_sched)
    resumed_param = fresh_model.weight.detach().clone()

    # Trajectory equality: next-step loss AND a sampled param match within 1e-6.
    assert abs(resumed_next_loss - ref_next_loss) < 1e-6
    assert torch.allclose(resumed_param, ref_param, atol=1e-6)


def test_open_dict_extensible(tmp_path):
    # An arbitrary extra key (the M2 EWC seam: fisher/theta_star) must round-trip,
    # and schema_version must be present — proving the dict is OPEN.
    model, opt, sched = _build()
    ckpt_path = tmp_path / "extra.pt"
    save_checkpoint(
        ckpt_path,
        model=model,
        optimizer=opt,
        scheduler=sched,
        step=0,
        model_config=ModelConfig(),
        train_config=TrainConfig(),
        git_sha="deadbeef",
        fisher={"x": 1},
    )
    raw = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    assert raw["schema_version"] == CKPT_SCHEMA_VERSION
    assert raw["fisher"] == {"x": 1}
    # Config travels inside the checkpoint (D-03 / QA-02 — no sidecar file).
    for key in ("model_config", "train_config", "git_sha", "rng"):
        assert key in raw


def test_records_git_sha(tmp_path):
    # git_sha() returns a non-empty string and lands inside the saved checkpoint (QA-02).
    sha = git_sha()
    assert isinstance(sha, str)
    assert sha != ""

    model, opt, sched = _build()
    ckpt_path = tmp_path / "sha.pt"
    save_checkpoint(
        ckpt_path,
        model=model,
        optimizer=opt,
        scheduler=sched,
        step=0,
        model_config=ModelConfig(),
        train_config=TrainConfig(),
        git_sha=sha,
    )
    raw = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    assert raw["git_sha"] == sha


def test_git_sha_fallback(monkeypatch):
    # With git unavailable, git_sha() returns "unknown" and never raises (Pitfall 4).
    def _boom(*a, **k):
        raise subprocess.CalledProcessError(128, "git")

    monkeypatch.setattr(subprocess, "run", _boom)
    assert git_sha() == "unknown"
