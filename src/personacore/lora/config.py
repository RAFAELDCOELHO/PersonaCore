"""LoRA configuration surface (LORA-01).

``LoRAConfig`` follows the ``ModelConfig`` house pattern (discretion resolution, 09-RESEARCH):
a plain dataclass with defaulted fields that travels as ``dataclasses.asdict()`` primitives —
both the open-dict ``**extra`` seam and the adapter artifact consume it.

``TARGET_PROJECTIONS`` is the canonical six-name allowlist. Injection iterates THESE names
explicitly — never a class-based ``isinstance`` scan over all Linears, which would pick up the
tied head and silently corrupt the input embedding for every token (PITFALLS P1).
"""

from dataclasses import dataclass

# Canonical allowlist: the six named nn.Linear projections per block (model/gpt.py seam,
# cross-pinned against tests/test_gpt_lora_seam.py::PROJECTIONS by tests/test_lora_inject.py).
TARGET_PROJECTIONS = ("q_proj", "k_proj", "v_proj", "c_proj", "fc_in", "fc_out")


@dataclass
class LoRAConfig:
    """Rank/alpha/dropout/targets for from-scratch LoRA injection (LORA-01)."""

    r: int = 8  # rank — 331,776 trainable params at production shape (~1.33 MB fp32 persona file).
    alpha: float = 16.0  # classic alpha/r convention -> scale 2.0 at defaults (pinned, P3).
    dropout: float = 0.0  # LoRA-branch dropout, applied to x before A (train mode only).
    targets: tuple[str, ...] = TARGET_PROJECTIONS  # immutable tuple — direct default is safe.
