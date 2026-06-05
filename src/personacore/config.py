"""Code-first config layer (D-01/D-02).

Three dataclasses split runtime/device concerns from model and training hyperparameters:

- ``RuntimeConfig`` — device + precision resolution. fp32 by default; AMP auto-disabled on
  CPU and MPS; bf16 RAISES on Pascal/P100 (compute capability < 7.0). This is the single
  source of device/AMP truth — nothing else in the codebase should call
  ``torch.cuda.is_available()``. Device priority is CUDA -> MPS (Apple Silicon) -> CPU.
- ``ModelConfig`` — model-sizing hyperparameters (vocab_size locked later by Phase 2).
- ``TrainConfig`` — training-loop hyperparameters.

The fp16-AMP + GradScaler *training path* is deliberately NOT implemented here — that is
Phase 3. Phase 1 only exposes the toggle and the bf16-on-Pascal guard (D-03).
"""

from dataclasses import dataclass, field

import torch


def _default_device() -> str:
    """Resolve the default device in priority order CUDA -> MPS -> CPU (D-02).

    CUDA (Kaggle P100) wins when present; otherwise MPS (Apple Silicon, the shipped
    Phase-5 training target per D-01) when available; otherwise CPU. ``torch.backends.mps``
    is exposed on all supported wheels (torch>=2.7), so the direct call is safe.
    """
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _is_pascal(device: str) -> bool:
    """True iff ``device`` names a CUDA GPU whose compute capability is Pascal-era (< 7.0).

    Pascal (sm_60, e.g. the Kaggle P100) has no Tensor Cores and no bf16 support. Guarded by
    ``startswith("cuda")`` + ``is_available()`` so it returns False on CPU-only machines.
    """
    if not device.startswith("cuda") or not torch.cuda.is_available():
        return False
    major, _minor = torch.cuda.get_device_capability(0)  # P100 -> (6, 0)
    return major < 7


@dataclass
class RuntimeConfig:
    """Centralized device + precision resolution (ENV-03)."""

    device: str = field(default_factory=_default_device)
    amp: bool = False  # fp32 DEFAULT.
    amp_dtype: str = "float16"  # P100 path is fp16 (NEVER bf16); toggled on in Phase 3.

    def __post_init__(self) -> None:
        if self.device in ("cpu", "mps"):
            # AMP is meaningless/unsupported on CPU; on MPS we hold fp32 only (D-02 — no
            # fp16 AMP on Apple Silicon). Both mirror the same fp32 posture: silently disable.
            self.amp = False
        if self.amp_dtype == "bfloat16" and _is_pascal(self.device):
            raise ValueError(
                "bf16 is unsupported on Pascal/P100 (compute capability < 7.0). "
                "Pascal has no Tensor Cores and no bfloat16 support — "
                "use fp32 (default) or fp16 AMP instead."
            )

    def autocast(self):
        """Return a ``torch.autocast`` context honoring this config's device/dtype/enabled."""
        return torch.autocast(
            device_type=self.device.split(":")[0],
            dtype=getattr(torch, self.amp_dtype),
            enabled=self.amp,
        )


@dataclass
class ModelConfig:
    """Model-sizing hyperparameters.

    ``vocab_size`` is now LOCKED by Phase 2 (the BPE tokenizer): 8192 is the load-bearing
    deliverable Phases 3-4 size the model around (D-01) and must never move. ``eos_id`` is the
    single shared atomic end-of-text id (D-03), top-pinned at 8184 (D-03a); it travels into the
    checkpoint automatically because ``save_checkpoint`` already ``asdict``s ``model_config``.
    """

    vocab_size: int = 8192  # LOCKED by Phase 2 (was the Phase-1 placeholder).
    eos_id: int = 8184  # shared atomic EOS id, recorded in checkpoint (D-03); top-pinned (D-03a).
    block_size: int = 256
    n_layer: int = 6
    n_head: int = 6
    n_embd: int = 384
    dropout: float = 0.0


@dataclass
class TrainConfig:
    """Training-loop hyperparameters (sensible defaults; overridden per run via kwargs/SHA)."""

    lr: float = 3e-4
    batch_size: int = 64
    max_steps: int = 5000
    warmup_steps: int = 100
    grad_clip: float = 1.0
    grad_accum_steps: int = 1
    weight_decay: float = 0.1
    seed: int = 1337
