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

Plan 09-02 adds the runtime semantics on top: the model-level enable/disable toggle plus the
exception-safe ``adapter_disabled`` context manager (D-05 / D-06) and full wrapper removal via
``eject_adapter`` (D-05's "Reset = drop adapter = instant forget" path).
"""

import contextlib

import torch
import torch.nn as nn

from .config import TARGET_PROJECTIONS, LoRAConfig
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


def set_adapter_enabled(model: nn.Module, enabled: bool) -> None:
    """Flip the ``enabled`` flag on every ``LoRALinear`` in the model (D-05 / D-06).

    The Phase-14 live memory-on/off demo drives THIS switch: disabling makes the flag-gated
    delta branch never execute, so the model is bit-identical to the pre-injection base; the
    A/B parameters are untouched, so re-enabling is an exact round-trip (LORA-05).
    """
    for m in model.modules():
        if isinstance(m, LoRALinear):
            m.enabled = enabled


@contextlib.contextmanager
def adapter_disabled(model: nn.Module):
    """Scoped, exception-safe adapter disable (D-06).

    Captures each module's PRIOR ``enabled`` value before disabling and restores those exact
    values in a ``finally`` block — a raising body still re-enables (D-06), and a module that
    was already disabled on entry stays disabled on exit (per-module restore, never blanket
    ``True``).
    """
    prior = {m: m.enabled for m in model.modules() if isinstance(m, LoRALinear)}
    for m in prior:
        m.enabled = False
    try:
        yield
    finally:
        for m, was_enabled in prior.items():
            m.enabled = was_enabled


def eject_adapter(model: nn.Module) -> int:
    """Return every wrapped projection to its plain base ``nn.Linear``; return the count.

    D-05's "Reset = drop adapter = instant forget" path: the wrappers are removed wholesale,
    the state-dict key set returns to vanilla GPT, and logits return EXACTLY to the
    pre-injection base. Walks parents exactly like ``inject_lora`` (allowlist names, P1).

    Asserts each child is unmerged first (Pitfall 6): eject while merged hands back
    adapter-contaminated base weights — unmerge first.
    """
    n = 0
    for parent in model.modules():
        for name in TARGET_PROJECTIONS:
            child = getattr(parent, name, None)
            if isinstance(child, LoRALinear):
                assert not child.merged, (
                    "eject while merged hands back adapter-contaminated base weights — "
                    "unmerge first (Pitfall 6)."
                )
                setattr(parent, name, child.base)
                n += 1
    return n


def merge_lora(model: nn.Module) -> None:
    """Fold every adapter delta into its base weight in place (LORA-04 / D-08 in-place form).

    Eval-time utility ONLY (Pitfall 6): a merged-state checkpoint double-counts the delta on
    reload, so the guard refuses in train mode — call ``model.eval()`` first; never checkpoint
    while merged. ``unmerge_lora`` restores bit-exactly via the stored clones (D-07).
    """
    assert model.training is False, (
        "merge_lora is an eval-time utility: call model.eval() first; "
        "never checkpoint while merged (Pitfall 6)."
    )
    for m in model.modules():
        if isinstance(m, LoRALinear):
            m.merge()


def unmerge_lora(model: nn.Module) -> None:
    """Bit-exact restore of every merged base weight from its stored clone (D-07)."""
    for m in model.modules():
        if isinstance(m, LoRALinear):
            m.unmerge()


def merged_state_dict(model: nn.Module) -> dict[str, torch.Tensor]:
    """PURE merged fold: a vanilla-GPT state dict, zero mutation of the live model (D-08).

    Phase 15's ΔW building block (and the deferred merged-slim export hook). For each wrapped
    projection the ``.base.weight`` key is de-infixed and its value computed out-of-place as
    ``base.weight + scale * (B @ A)``; ``.base.bias`` is de-infixed; ``lora_A``/``lora_B``
    keys are dropped; everything else passes through. All values are detached clones, so the
    result shares no storage with the live model.
    """
    with torch.no_grad():
        wrapped = {prefix: m for prefix, m in model.named_modules() if isinstance(m, LoRALinear)}
        # Guard the fold the same way merge() does: folding an already-merged base weight
        # would silently double-count the delta (Pitfall 6 / T-09-04).
        for prefix, m in wrapped.items():
            assert not m.merged, f"merged_state_dict on a merged model ({prefix}) — unmerge first"
        weight_keys = {f"{p}.base.weight": (f"{p}.weight", m) for p, m in wrapped.items()}
        bias_keys = {f"{p}.base.bias": f"{p}.bias" for p in wrapped}
        out: dict[str, torch.Tensor] = {}
        for key, value in model.state_dict().items():
            if key.endswith(".lora_A") or key.endswith(".lora_B"):
                continue  # adapter factors never enter the merged dict.
            if key in weight_keys:
                new_key, m = weight_keys[key]
                delta = m.scale * (m.lora_B @ m.lora_A)  # reads self.scale (P3).
                out[new_key] = (m.base.weight + delta).detach().clone()
            elif key in bias_keys:
                out[bias_keys[key]] = value.detach().clone()
            else:
                out[key] = value.detach().clone()
        return out
