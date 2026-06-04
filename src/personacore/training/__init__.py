"""Training harness (D-09) — the public surface: loop, loss assembly, LR schedule, data path.

Plan 04 owns this barrel (Plan 03 deliberately left ``training/`` namespace-only). It re-exports
the four modules the harness and its scripts/tests import from a single place — mirroring the
``personacore.tokenizer`` package surface — so callers write ``from personacore.training import
train`` instead of reaching into submodules.
"""

from .data import get_batch, load_split
from .loop import estimate_loss, sample, train
from .loss import assemble_loss
from .schedule import build_lr_lambda, build_scheduler

__all__ = [
    "assemble_loss",
    "build_lr_lambda",
    "build_scheduler",
    "estimate_loss",
    "get_batch",
    "load_split",
    "sample",
    "train",
]
