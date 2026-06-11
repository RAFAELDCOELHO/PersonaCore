"""Phase 9 — from-scratch LoRA (LORA-01..05): public import surface.

Plan 09-01 ships the config (``LoRAConfig``/``TARGET_PROJECTIONS``), the ``LoRALinear``
composition wrapper, and the post-load injection/freeze machinery; plan 09-02 adds the
toggle/eject runtime semantics (D-05 / D-06) and the merge utilities (D-07 / D-08); later
plans extend ``__all__`` with the adapter artifact seam.
"""

from .config import TARGET_PROJECTIONS, LoRAConfig
from .inject import (
                     adapter_disabled,
                     eject_adapter,
                     inject_lora,
                     load_adapter_weights,
                     lora_state_dict,
                     mark_only_lora_trainable,
                     merge_lora,
                     merged_state_dict,
                     set_adapter_enabled,
                     snapshot_params,
                     unmerge_lora,
)
from .layer import LoRALinear

__all__ = [
    "LoRAConfig",
    "LoRALinear",
    "TARGET_PROJECTIONS",
    "adapter_disabled",
    "eject_adapter",
    "inject_lora",
    "load_adapter_weights",
    "lora_state_dict",
    "mark_only_lora_trainable",
    "merge_lora",
    "merged_state_dict",
    "set_adapter_enabled",
    "snapshot_params",
    "unmerge_lora",
]
