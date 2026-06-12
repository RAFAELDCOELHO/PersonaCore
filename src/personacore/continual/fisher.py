"""Per-example empirical diagonal Fisher estimation (EWC-01, D-01..D-05).

``estimate_fisher`` computes the empirical diagonal Fisher of the model at its CURRENT weights
over windows of a uint16 memmap corpus, via a strict batch=1 loop (D-03): one block_size window
is one example; per example it runs the model's OWN forward (``_, loss = model(x, y)`` — the
LOCKED CE tail with its mean-over-tokens reduction; never a reimplemented cross-entropy,
Pitfall 6), takes per-example gradients with ``torch.autograd.grad``, and accumulates ``g**2``
in fp32 on device. Squaring a gradient aggregated over a batch > 1 is NOT the Fisher — the
cross-terms do not vanish (the van de Ven bug, Pitfall 2) — which is why the batch=1 loop is
the law here and a unit test pins the distance to the batched estimate.

Normalization (D-01/D-02): after averaging over the N examples, every tensor is divided by the
global mean over ALL trainable coordinates (deduped — the tied ``wte``/``lm_head`` storage
appears exactly once because iteration uses ``model.named_parameters()``), so ``mean(F) = 1``
and lambda reads as stiffness relative to an average parameter. The raw scalar divisor is
recorded in ``fisher_meta["normalizer"]`` so the unnormalized estimate is recoverable.

RNG purity (Pitfall 3): window starts come from a LOCAL ``np.random.default_rng(seed)`` — one
``int(rng.integers(0, data_len - block_size - 1))`` call per example, in example order (this
exact draw pattern is pinned by the oracle test, so tests can re-derive the windows). Global
python/numpy/torch RNG streams are never touched: ``torch.random.fork_rng`` would not cover
numpy, and the eval-mode forward consumes no torch RNG. The memmap is re-opened per draw (the
RSS discipline from ``training/data.py::get_batch_memmap``, whose GLOBAL numpy draws this
module deliberately does NOT share).

Convergence evidence (D-05): the N examples feed two disjoint half-accumulators; the halves
are compared via a hand-rolled ordinal-rank Spearman (double argsort + ``np.corrcoef`` — scipy
is not a dependency) plus the relative mean change of each half vs the full estimate, all in
fp64 on CPU (MPS has no fp64 — Pitfall 4). "N is enough" is thereby a measured claim, reported
in ``fisher_meta``, not gated.

Fail-loud guards (Pitfall 7): non-finite accumulated tensors or a non-positive raw global mean
raise ``ValueError`` naming the failure before anything is returned — a degenerate normalizer
would silently poison everything downstream. There is no ``no_grad`` context anywhere
(gradients ARE the product) and no autocast (fp32-only by design; fp16 squared gradients
underflow on the P100 fallback). The prior ``model.training`` flag is restored on exit.
"""

import numpy as np
import torch

__all__ = ["estimate_fisher"]

_VARIANT = "empirical_diag_fisher/groundtruth_targets/mean_normalized"
_SPEARMAN_METHOD = "ordinal_double_argsort_no_tie_averaging"


def _spearman(a, b):
    """Ordinal-rank Spearman correlation (no tie-averaging), fp64 — Pearson on double-argsort
    ranks. Hand-rolled: scipy is NOT a dependency (zero-new-deps posture)."""
    ra = np.empty(len(a), dtype=np.float64)
    ra[np.argsort(a)] = np.arange(len(a), dtype=np.float64)
    rb = np.empty(len(b), dtype=np.float64)
    rb[np.argsort(b)] = np.arange(len(b), dtype=np.float64)
    return float(np.corrcoef(ra, rb)[0, 1])


def _flat64(tensors):
    """Flatten a list of fp32 CPU tensors into one fp64 numpy vector (statistics domain)."""
    return np.concatenate([t.numpy().astype(np.float64).ravel() for t in tensors])


def estimate_fisher(model, bin_path, *, n_examples, block_size, device, seed, normalize=True):
    """Per-example empirical diagonal Fisher at the model's current weights (EWC-01, D-03).

    Args:
        model: The GPT (or any ``(x, y) -> (logits, loss)`` module); evaluated in eval mode,
            prior training flag restored on exit. Iteration uses ``named_parameters()`` so the
            tied ``wte``/``lm_head`` tensor contributes exactly once (under ``wte.weight``).
        bin_path: Flat uint16 memmap corpus (``train.bin``); re-opened per draw (RSS discipline).
        n_examples: N independent batch=1 windows (D-04 production budget ~2000); must be >= 2
            so the D-05 half-split convergence check is defined.
        block_size: Window length; one window = one example (D-03).
        device: Where forward/grad/accumulation run (fp32 accumulators live here).
        seed: Seeds the LOCAL ``np.random.default_rng`` for window starts — the draw pattern is
            one ``int(rng.integers(0, data_len - block_size - 1))`` per example, in order.
        normalize: When True (default), divide all tensors by the raw global mean (D-01/D-02).

    Returns:
        ``(fisher, fisher_meta)`` — ``fisher``: ``{param_name: fp32 CPU tensor}`` with shapes
        matching the parameters and keys from ``named_parameters()``; ``fisher_meta``:
        primitives only (``weights_only=True``-safe), exact key set: variant, n_examples, seed,
        block_size, bin_path, normalized, normalizer, spearman_half, rel_mean_change_a,
        rel_mean_change_b, spearman_method.
    """
    if n_examples < 2:
        raise ValueError(
            f"estimate_fisher: n_examples must be >= 2 for the half-split convergence check "
            f"(D-05), got {n_examples}."
        )
    data_len = len(np.memmap(bin_path, dtype=np.uint16, mode="r"))
    if data_len <= block_size + 1:
        raise ValueError(
            f"estimate_fisher: corpus {bin_path} has {data_len} tokens — too short for "
            f"block_size={block_size} windows (need > block_size + 1)."
        )

    was_training = model.training
    model.eval()  # eval discipline (dropout is 0.0 in this config anyway — Pitfall 6).
    try:
        named = list(model.named_parameters())  # tied tensor appears ONCE (session-verified).
        names = [n for n, _ in named]
        params = [p for _, p in named]

        rng = np.random.default_rng(seed)  # LOCAL generator — global RNG untouched (Pitfall 3).
        acc_a = [torch.zeros_like(p, device=device, dtype=torch.float32) for p in params]
        acc_b = [torch.zeros_like(p, device=device, dtype=torch.float32) for p in params]
        n_half = n_examples // 2

        for i in range(n_examples):
            data = np.memmap(bin_path, dtype=np.uint16, mode="r")  # re-open per draw (RSS).
            start = int(rng.integers(0, data_len - block_size - 1))
            x = torch.from_numpy(data[start : start + block_size].astype(np.int64))[None].to(device)
            y = torch.from_numpy(data[start + 1 : start + 1 + block_size].astype(np.int64))[
                None
            ].to(device)
            _, loss = model(x, y)  # the model's OWN CE — matched mean-over-tokens reduction.
            grads = torch.autograd.grad(loss, params)  # per-example grads, no .grad mutation.
            acc = acc_a if i < n_half else acc_b  # two disjoint half-accumulators (D-05).
            for a, g in zip(acc, grads):
                a.add_(g.detach().float() ** 2)

        full = [(a + b) / float(n_examples) for a, b in zip(acc_a, acc_b)]

        # Fail-loud guards (Pitfall 7) — before any statistics or division.
        for name, t in zip(names, full):
            if not torch.isfinite(t).all():
                raise ValueError(
                    f"estimate_fisher: non-finite Fisher entries in {name!r} — corrupt window "
                    "or diverged weights (Pitfall 7)."
                )

        # Statistics in fp64 AFTER moving to CPU (MPS has no fp64 — Pitfall 4).
        full_cpu = [t.detach().float().cpu() for t in full]
        normalizer = float(_flat64(full_cpu).mean())
        if not (np.isfinite(normalizer) and normalizer > 0.0):
            raise ValueError(
                f"estimate_fisher: degenerate raw global mean {normalizer!r} — all-zero "
                "gradients or non-finite accumulation; refusing to normalize (Pitfall 7)."
            )

        # D-05 convergence stats over the RAW half-estimates, fp64 on CPU.
        half_a = _flat64([(a / float(n_half)).detach().float().cpu() for a in acc_a])
        half_b = _flat64([(b / float(n_examples - n_half)).detach().float().cpu() for b in acc_b])
        spearman_half = _spearman(half_a, half_b)
        rel_mean_change_a = float(abs(half_a.mean() - normalizer) / normalizer)
        rel_mean_change_b = float(abs(half_b.mean() - normalizer) / normalizer)

        if normalize:
            fisher = {n: t / normalizer for n, t in zip(names, full_cpu)}
        else:
            fisher = dict(zip(names, full_cpu))

        fisher_meta = {
            "variant": _VARIANT,
            "n_examples": int(n_examples),
            "seed": int(seed),
            "block_size": int(block_size),
            "bin_path": str(bin_path),
            "normalized": bool(normalize),
            "normalizer": normalizer,
            "spearman_half": spearman_half,
            "rel_mean_change_a": rel_mean_change_a,
            "rel_mean_change_b": rel_mean_change_b,
            "spearman_method": _SPEARMAN_METHOD,
        }
    finally:
        # Restore the PRIOR flag on EVERY exit — success AND the fail-loud guard raises above
        # (the docstring contract: "The prior ``model.training`` flag is restored on exit").
        # Without this, a caught ValueError left the model silently stuck in eval mode.
        if was_training:
            model.train()
    return fisher, fisher_meta
