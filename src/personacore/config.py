"""Code-first config layer (D-01/D-02).

Three dataclasses split runtime/device concerns from model and training hyperparameters:

- ``RuntimeConfig`` — device + precision resolution. fp32 by default; AMP auto-disabled on
  CPU; bf16 RAISES on Pascal/P100 (compute capability < 7.0). This is the single source of
  device/AMP truth — nothing else in the codebase should call ``torch.cuda.is_available()``.
- ``ModelConfig`` — model-sizing hyperparameters (vocab_size locked later by Phase 2).
- ``TrainConfig`` — training-loop hyperparameters.

The fp16-AMP + GradScaler *training path* is deliberately NOT implemented here — that is
Phase 3. Phase 1 only exposes the toggle and the bf16-on-Pascal guard (D-03).
"""

from dataclasses import dataclass, field

import torch


def _default_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


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
        if self.device == "cpu":
            # AMP is meaningless/unsupported on CPU — silently disable.
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

    ``vocab_size`` is a placeholder default here; Phase 2 (the BPE tokenizer) locks the real
    value. Do not finalize it in Phase 1.
    """

    vocab_size: int = 50304  # placeholder — locked by Phase 2.
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
