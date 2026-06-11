"""Phase 9 — from-scratch LoRA (LORA-01..05): public import surface.

Plan 09-01 ships the config (``LoRAConfig``/``TARGET_PROJECTIONS``), the ``LoRALinear``
composition wrapper, and the post-load injection/freeze machinery; later plans extend
``__all__`` with toggle/eject (09-02) and merge utilities (09-03).
"""

from .config import TARGET_PROJECTIONS, LoRAConfig
from .layer import LoRALinear

__all__ = ["LoRAConfig", "LoRALinear", "TARGET_PROJECTIONS"]
