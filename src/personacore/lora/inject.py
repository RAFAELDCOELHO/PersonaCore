"""Post-load injection, freeze discipline, and key-audited adapter apply (LORA-01 / LORA-02).

Ordering is load-bearing: build vanilla GPT -> load base weights -> ``inject_lora`` ->
``mark_only_lora_trainable``. Wrapping grows every wrapped projection's state-dict keys with a
``.base.`` infix, so injecting before loading would break every saved key.

Allowlist discipline (PITFALLS P1): injection iterates ``cfg.targets`` (the canonical
``TARGET_PROJECTIONS`` six names) explicitly — never an ``isinstance`` scan over all Linears,
which would pick up the tied output head and silently corrupt the input embedding.

Key-audit discipline (PITFALLS P4): ``load_adapter_weights`` raises ``ValueError`` on any
key-set mismatch BEFORE loading a single tensor — a bare ``strict=False`` load is banned; the
exact-equality audit is what makes the subsequent ``strict=False`` call legitimate.
"""

import torch
import torch.nn as nn

from .config import LoRAConfig
from .layer import LoRALinear


def inject_lora(model: nn.Module, cfg: LoRAConfig) -> int:
    """Wrap every allowlisted ``nn.Linear`` projection in ``LoRALinear``; return the count.

    Walks ``model.modules()`` as parents and replaces exactly the ``cfg.targets`` child names
    via ``setattr`` (PITFALLS P1 — explicit allowlist only). Callers assert the returned count
    equals ``6 * n_layer``.
    """
    n = 0
    for parent in model.modules():
        for name in cfg.targets:  # explicit allowlist — NEVER an isinstance scan (P1).
            child = getattr(parent, name, None)
            if isinstance(child, nn.Linear):
                setattr(parent, name, LoRALinear(child, cfg.r, cfg.alpha, cfg.dropout))
                n += 1
    return n


def mark_only_lora_trainable(model: nn.Module) -> None:
    """Freeze everything, then re-enable exactly the LoRA A/B parameters (LORA-02).

    Name-suffix traversal (the ``gpt.py`` residual-scaled-init idiom): trainable census after
    this call equals ``r * n_layer * 18 * n_embd`` (closed form verified in 09-RESEARCH.md).
    """
    model.requires_grad_(False)
    for name, p in model.named_parameters():
        if "lora_" in name:
            p.requires_grad_(True)


def snapshot_params(model: nn.Module) -> dict[str, torch.Tensor]:
    """Detached clones of every named parameter — the params-actually-update canary helper.

    Reused by the training tests and the Plan-04 smoke script: after >=1 optimizer step, every
    trainable param must have moved and every frozen param must be bit-identical (LORA-02).
    """
    return {n: p.detach().clone() for n, p in model.named_parameters()}


def lora_state_dict(model: nn.Module) -> dict[str, torch.Tensor]:
    """Filter the model state dict down to ``lora_`` keys — the adapter dict (LORA-03 seam).

    Base weights never leak into the shareable persona file: only ``lora_A``/``lora_B``
    tensors pass the filter.
    """
    return {k: v for k, v in model.state_dict().items() if "lora_" in k}


def load_adapter_weights(model: nn.Module, artifact: dict) -> None:
    """Apply an adapter dict onto an injected model behind an exact key-set audit (P4).

    Raises ``ValueError`` naming the symmetric difference BEFORE any tensor is loaded when
    ``artifact["adapter"]`` keys do not exactly match the model's ``lora_`` keys.
    """
    expected = {k for k in model.state_dict() if "lora_" in k}
    got = set(artifact["adapter"].keys())
    if expected != got:
        missing = sorted(expected - got)
        unexpected = sorted(got - expected)
        raise ValueError(
            f"adapter key-set mismatch: missing={missing} unexpected={unexpected} — "
            "the artifact does not describe this injected model; refusing to load."
        )
    model.load_state_dict(artifact["adapter"], strict=False)
