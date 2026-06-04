"""Process-global seeding for reproducible runs (ENV-05).

``seed_everything`` seeds every RNG a training run touches — Python ``random``, NumPy,
and torch (CPU + all CUDA devices when present) — and disables the cuDNN autotuner so GPU
runs don't drift run-to-run (Pitfall 3).

Call this ONCE at the start of a FRESH run. On RESUME, do NOT call it — ``load_checkpoint``
restores the captured generator STATE instead (re-seeding would rewind the stream to step 0
and break trajectory equality — Pitfall 2).

``strict=True`` opts into full bitwise determinism (deterministic algorithms + cuDNN
deterministic kernels + the cuBLAS workspace env var). It is OFF by default (Open Question 3)
because deterministic ops are slower; the portfolio reproducibility guarantee is
seed + git SHA + config, with full GPU determinism available but optional.
"""

import os
import random

import numpy as np
import torch


def seed_everything(seed: int, *, strict: bool = False) -> None:
    """Seed random/numpy/torch(+cuda) for a fresh run.

    Args:
        seed: The integer seed applied to every RNG stream.
        strict: When True, additionally enable deterministic algorithms, cuDNN
            deterministic kernels, and set ``CUBLAS_WORKSPACE_CONFIG`` for full bitwise
            reproducibility. Slower — opt-in only (default False).
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)  # seeds CPU and, when present, CUDA generators
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False  # disable the autotuner (nondeterministic)

    if strict:
        # Full determinism — measurably slower; documented trade-off (CLAUDE.md).
        torch.use_deterministic_algorithms(True)
        torch.backends.cudnn.deterministic = True
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
