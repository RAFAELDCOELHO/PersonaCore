"""Frozen-base adapter training pins through the UNTOUCHED v1.0 ``train()`` (LORA-02 / D-04).

These tests prove the load-bearing Phase-9 training claim WITHOUT a single edit to
``training/loop.py``: ``mark_only_lora_trainable`` + the existing ``AdamW(model.parameters())``
construction is already frozen-param safe (09-RESEARCH Pattern 3, empirically verified) — frozen
params get no step, no decoupled weight decay, and NO optimizer-state entries. Four pins:

1. **Canary + grad isolation (LORA-02).** After an adapter run, every ``requires_grad`` param has
   moved (``not torch.equal``) and every frozen base param is BIT-identical (``torch.equal``) to
   its pre-training snapshot.
2. **Optimizer-state scope.** The ``train()``-saved checkpoint's AdamW state holds entries ONLY
   for the stepped A/B params — ``12 * n_layer`` (2 lora tensors x 6 wrapped modules per layer).
3. **Kill+resume (D-04).** Adapter training resumes the SAME trajectory as an uninterrupted run
   via the deterministic vanilla -> inject -> freeze reconstruction order (the
   ``test_resume_curve.py`` template on an injected GPT).
4. **``lora_config`` rides ``**extra``.** The open-dict seam carries the adapter config so the
   resume path can rebuild the module tree from the checkpoint alone.

CANARY MATH CAVEAT — the run MUST contain >= 2 effective (nonzero-lr) optimizer steps: with the
B=0 identity gate at init, dL/dA flows THROUGH B, so ``lora_A``'s gradient is identically ZERO on
the first step — and with ``weight_decay=0.0`` the A matrices are bit-unchanged after exactly one
step. Step 1 moves B off zero; only step >= 2 moves A. A future refactor of these tests to a
1-step canary MUST fail review loudly: it would pass for B and silently stop proving A trains.
(The warmup lambda is ``(step + 1) / warmup_steps`` — lr is nonzero from step 1, so all 6 steps
here are effective.)

The adapter-run ``TrainConfig`` overrides ``weight_decay`` to 0.0: the 0.1 default would decay
frozen-adjacent dynamics AND fights the low-rank update (09-RESEARCH Pattern 3). CPU-only,
GPU-free: ``RuntimeConfig(device="cpu")`` is pinned explicitly so snapshots and post-train params
share a device (``torch.equal`` raises cross-device) even on an MPS-capable host.
"""

from dataclasses import asdict

import torch

from personacore.checkpoint import save_checkpoint
from personacore.config import ModelConfig, RuntimeConfig, TrainConfig
from personacore.lora import (
    TARGET_PROJECTIONS,
    LoRAConfig,
    LoRALinear,
    inject_lora,
    mark_only_lora_trainable,
    snapshot_params,
)
from personacore.model import GPT
from personacore.seeding import seed_everything
from personacore.training.loop import train


def _tiny_cfg() -> ModelConfig:
    return ModelConfig(block_size=32, n_layer=1, n_head=2, n_embd=16)


def _adapter_cfg() -> TrainConfig:
    # weight_decay MUST be 0.0 for adapter runs (overriding the 0.1 default) — see module
    # docstring. 6 steps so lora_A provably moves (>= 2 effective steps after B leaves zero).
    return TrainConfig(lr=1e-2, warmup_steps=2, max_steps=6, batch_size=4, weight_decay=0.0)


def _cpu_runtime() -> RuntimeConfig:
    # Pin CPU so the suite stays GPU-free and same-device for torch.equal on an MPS host.
    return RuntimeConfig(device="cpu")


def _build_injected(lora_cfg: LoRAConfig) -> GPT:
    # The deterministic reconstruction order — vanilla GPT -> inject -> freeze — identical on
    # resume, so AdamW param indices re-associate deterministically (09-RESEARCH Pattern 3).
    model = GPT(_tiny_cfg())
    inject_lora(model, lora_cfg)
    mark_only_lora_trainable(model)
    return model


def _fixed_batch(cfg: ModelConfig):
    xb = torch.randint(0, cfg.vocab_size, (4, cfg.block_size))
    yb = torch.randint(0, cfg.vocab_size, (4, cfg.block_size))
    return xb, yb


def _first_lora(model) -> LoRALinear:
    return next(m for m in model.modules() if isinstance(m, LoRALinear))


def test_canary_and_frozen_base_bit_untouched():
    # LORA-02 — the phase's load-bearing training test: trainables moved, base bit-untouched.
    seed_everything(1234)
    model = _build_injected(LoRAConfig(r=4))
    batch = _fixed_batch(_tiny_cfg())
    before = snapshot_params(model)
    train(
        train_config=_adapter_cfg(),
        runtime_config=_cpu_runtime(),
        model=model,
        model_config=_tiny_cfg(),
        fixed_batch=batch,
    )
    for n, p in model.named_parameters():
        if p.requires_grad:
            assert not torch.equal(p, before[n]), f"trainable {n} did not move (canary)"
        else:
            assert torch.equal(p, before[n]), f"frozen base param {n} changed bit-level"


def test_optimizer_state_scoped_to_lora_params(tmp_path):
    # AdamW holds moments ONLY for stepped params (RESEARCH-verified, pinned vs regression):
    # no state bloat for the frozen base in the train()-saved checkpoint.
    seed_everything(1234)
    cfg = _tiny_cfg()
    model = _build_injected(LoRAConfig(r=4))
    ckpt_path = tmp_path / "latest.pt"
    train(
        train_config=_adapter_cfg(),
        runtime_config=_cpu_runtime(),
        model=model,
        model_config=cfg,
        fixed_batch=_fixed_batch(cfg),
        checkpoint_path=ckpt_path,
    )
    # weights_only=False: OWN trusted file this test just wrote (the loop's resume-path idiom).
    ckpt = torch.load(ckpt_path, weights_only=False)
    # 2 lora tensors x 6 wrapped modules = 12 stepped params per layer (tiny fixture: 12 total).
    assert len(ckpt["optimizer"]["state"]) == 12 * cfg.n_layer


def test_adapter_kill_resume_identical_trajectory(tmp_path):
    # D-04 — adapting tests/test_resume_curve.py to the injected model: a killed-and-resumed
    # adapter run continues the SAME trajectory as an uninterrupted one.
    cfg = _tiny_cfg()
    adapter_cfg = _adapter_cfg()

    # --- Reference: an uninterrupted run of all 6 steps ---
    seed_everything(1234)
    ref_model = _build_injected(LoRAConfig(r=4))
    ref_batch = _fixed_batch(cfg)
    ref_loss = train(
        train_config=adapter_cfg,
        runtime_config=_cpu_runtime(),
        model=ref_model,
        model_config=cfg,
        fixed_batch=ref_batch,
        return_final_loss=True,
    )
    ref_B = _first_lora(ref_model).lora_B.detach().clone()

    # --- Resumed: run half, checkpoint, KILL, fresh deterministic rebuild, resume to the end ---
    seed_everything(1234)
    half_model = _build_injected(LoRAConfig(r=4))  # SAME construction order -> same RNG stream
    half_batch = _fixed_batch(cfg)  # identical values to ref_batch (same RNG point)
    ckpt_path = tmp_path / "latest.pt"
    train(
        train_config=adapter_cfg,
        runtime_config=_cpu_runtime(),
        model=half_model,
        model_config=cfg,
        fixed_batch=half_batch,
        max_steps_override=3,
        checkpoint_path=ckpt_path,
    )

    fresh_model = _build_injected(LoRAConfig(r=4))  # vanilla -> inject -> freeze, then restore
    resumed_loss = train(
        train_config=adapter_cfg,
        runtime_config=_cpu_runtime(),
        model=fresh_model,
        model_config=cfg,
        fixed_batch=half_batch,
        resume_from=ckpt_path,
        return_final_loss=True,
    )
    resumed_B = _first_lora(fresh_model).lora_B.detach().clone()

    # Trajectory equality within 1e-6 (the checkpoint restores RNG STATE, not a re-seed).
    assert abs(float(resumed_loss) - float(ref_loss)) < 1e-6
    assert torch.allclose(resumed_B, ref_B, atol=1e-6)


def test_lora_config_rides_checkpoint_extra(tmp_path):
    # D-04 open-dict seam: lora_config travels via save_checkpoint(**extra) and reloads intact,
    # so the resume path can rebuild the injected module tree from the checkpoint alone.
    seed_everything(1234)
    model = _build_injected(LoRAConfig(r=4))
    path = tmp_path / "with_extra.pt"
    save_checkpoint(
        path,
        model=model,
        optimizer=torch.optim.AdamW(model.parameters()),
        scheduler=None,
        step=1,
        model_config=_tiny_cfg(),
        train_config=_adapter_cfg(),
        git_sha="testsha",
        lora_config=asdict(LoRAConfig(r=4)),
    )
    ckpt = torch.load(path, weights_only=False)  # own trusted file the test just wrote
    assert ckpt["lora_config"]["r"] == 4
    assert tuple(ckpt["lora_config"]["targets"]) == TARGET_PROJECTIONS
