"""Phase 19 selective memory erasure — THE PRE-REGISTRATION (ERASE-01, STAT-05).

ORDERING CONTRACT
=================
Read this before editing anything below it.

**1. This file IS the Phase 19 pre-registration, and every commit touching it must be an ANCESTOR
of the first-add commit of every ``results/phase19_*`` artifact.** Every commit, not merely the
first: a pin asserting only "the file existed before the number" still permits the manoeuvre it
exists to forbid — rewriting a rule once the number it judges is visible.
``tests/test_phase16_prereg.py::test_phase19_prereg_is_frozen_before_every_phase19_result`` asks
git's object graph, never a committer date, for the same reason its Phase 17 and Phase 18 twins do:
a committer date is rewritable by anyone with a shell, non-monotonic after a rebase, and skewed
across machines. Ancestry is a property of the DAG, and making ``git merge-base --is-ancestor`` lie
requires rewriting every object between the two commits, which changes both SHAs.

**2. NO ``results/phase19_*`` artifact may be committed until the pin is COMPLETE at plan 19-07.**
The pin lands across plans 19-01..19-06 — the mechanism (here), the target fact and the denominator,
the blind-calibration floor and its reachability proof, the estimators, the arm runners and the
report text — and 19-07 audits the finished article. A Phase 19 number committed before then is a
number whose own rule was still being written. That ordering IS the scientific guarantee of this
phase; it is not bookkeeping, and no plan may trade it away for convenience.

**3. After 19-07 this file is permanently uneditable.** ``scripts/phase17_personas.py`` reached that
state at ``d549e0b`` and ``scripts/phase18_extraction.py`` at ``99716e0`` — in both cases the moment
the phase's first result artifact was committed. The recovery path for a genuine defect discovered
afterwards is a DATED CONTINUATION published beside the original text (``scripts/_addendum.py``,
decision D3), never an edit and never a ``--force`` flag. Editing a recorded rule after its number
exists destroys the only thing that made the rule worth recording.

WHAT THIS FILE HOLDS AT PLAN 19-01, AND WHAT IT DELIBERATELY DOES NOT
--------------------------------------------------------------------
Holds: the ordering contract above, the mechanism identity and its rule, the DERIVED component
index, and the ablation operator. That is the whole of it. The calibrated floor, the target fact,
the denominators, the noise-floor estimators and the report text are plans 19-02..19-05, and
writing any of them here early would mean fixing them before the plan that reasons about them.

Success criteria are INHERITED from ``scripts/erasure_gate.py`` (committed ``23a830c``, 2026-08-12
16:27:43 -0300, before Phase 16 ran) and are never re-authored here. That file fixed the BAR and
deliberately fixed no design; this file commits the DESIGN it left open, and touches no bar.

Nothing executes at import beyond the ``sys.path`` bootstrap below and the derived-census proof at
the foot of the file. CPU-only, GPU-free, no checkpoint read, no network.
"""

import pathlib
import sys

from personacore.lora import LoRAConfig

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# `scripts/` is sys.path[0] only when a script in it is run DIRECTLY; an importlib-loaded test
# harness gets no such entry (phase18_extraction.py:41-46 precedent). Insert it explicitly so the
# sibling driver below is reachable from both paths. This is the ONE module-level side effect this
# file is permitted.
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

# The 36-key (layer, projection, state_dict_key) enumeration is IMPORTED, never re-derived. It is
# already a committed explicit product over `TARGET_PROJECTIONS` x `N_LAYER` with the "never an
# isinstance scan" discipline recorded on it (extract_deltas.py:94-102), and a second copy of an
# enumeration is a copy free to stop agreeing with the first.
import extract_deltas  # noqa: E402  (needs the sys.path insert above)


def _prove(condition, message):
    """Loud proof: ``SystemExit`` naming the violated contract (never an ``-O``-strippable one).

    Same register and same reason as ``phase14_recall._prove`` (``:221-224``),
    ``phase16_persistence._prove``, ``phase17_isolation._prove`` and
    ``phase18_extraction._prove`` (``:56``), with this module's own prefix — an abort naming the
    wrong driver sends its reader to the wrong file.
    """
    if not condition:
        raise SystemExit(f"[phase19_erasure] PROOF FAILED: {message}")


# =============================================================================================
# ===== THE MECHANISM — pinned here, before the blind calibration runs =====
# =============================================================================================

MECHANISM_ID = "M1-rank1-component-ablation"

MECHANISM_RULE = (
    "PRIMARY MECHANISM (M1, id 'M1-rank1-component-ablation'): erasure is performed by ZEROING "
    "rank-1 components of the LoRA delta. `LoRALinear.forward` computes `y = base(x) + scale * (x "
    "@ A^T @ B^T)` (layer.py:38-42), i.e. `dW = scale * (B @ A)` with `B: (out, r)` and `A: (r, "
    "in)`, which is exactly the sum over j of `scale * outer(B[:, j], A[j, :])` — r rank-1 outer "
    "products per wrapped projection. The surgery surface is therefore the address `(layer, "
    "projection, j)`, and its size is DERIVED from the committed wrap set and the committed rank "
    "(see `component_index`), never typed. Ablating a component means zeroing BOTH `B[:, j]` and "
    "`A[j, :]`.",
    "WHY M1 AND NOT SOMETHING STRONGER: staying inside the rank-r decomposition is what keeps the "
    "erased model exactly representable in the SHIPPED artifact format. The erased adapter has the "
    "same keys, the same shapes, the same dtypes and the same `lora_config`, so it round-trips "
    "through `export_adapter`/`load_adapter` and passes `load_adapter_weights`' key, shape AND "
    "scale audits (inject.py:76-131) with none of them relaxed. It also leaves the adapter-off "
    "bit-identity control untouched: with the adapter disabled the wrapper's forward is literally "
    "`self.base(x)`, so an operator that only rewrites `lora_A`/`lora_B` cannot move the "
    "adapter-off logits at all (`run_bit_identity_control`, phase14_recall.py:1480). A mechanism "
    "that edited base weights would have to re-earn both properties.",
    "REFERENCE ARM (M2, ERASE-02): retrain the adapter from the same base under the same recipe on "
    "the taught fact set MINUS the target — the 'never learned it' arm. It is a REFERENCE, not a "
    "second erasure mechanism: it answers 'what would the weights look like if this fact had never "
    "been taught', which is the only honest comparison for an erasure claim at this scale. It is "
    "not a fallback M1 may be replaced by.",
    "DECLINED, NOT DEFERRED (D1): M3 (retain-set continued fine-tuning), M4 (Fisher-anchored "
    "damping), M5 (task-arithmetic negation) and M6 (gradient ascent) are OUT of this phase. They "
    "are not scheduled elsewhere and are not being kept in reserve. The M1/M2 pair answers the "
    "phase's central question, and a third arm is unguaranteed scope. Recording this as a decline "
    "rather than a deferral matters: a deferred mechanism is one a disappointing result can "
    "reach for.",
    "THE MECHANISM AND ITS PARAMETERS ARE PINNED BEFORE THE BLIND CALIBRATION RUNS (D1). A "
    "mechanism chosen or swapped after a disappointing floor is not a pre-registered mechanism, in "
    "exactly the sense a threshold chosen after seeing the data is not a threshold. The stopping "
    "rule that decides HOW MUCH to ablate is pinned in the same file before any calibration or "
    "erasure executes; this clause is what forbids it becoming a knob afterwards.",
)

# =============================================================================================
# ===== THE COMPONENT INDEX AND THE ABLATION OPERATOR =====
# =============================================================================================

# The committed production rank, READ from the dataclass default rather than retyped
# (lora/config.py:23 — "r=8, 331,776 trainable params at production shape"). `alpha` is not read
# here on purpose: this module never recomputes `alpha / r`. `LoRALinear.scale` is the single
# source of truth for it (layer.py:27, PITFALLS P3) and the ablation operator never touches it.
PRODUCTION_RANK = LoRAConfig().r

# (layer, projection) -> the adapter-artifact key prefix. The `.weight` suffix is stripped exactly
# as `extract_deltas.adapter_cells` does it (:183) — injection rewrites a wrapped projection's
# state-dict keys with a `.base.` infix, so the projection's own prefix is what carries `lora_A`
# and `lora_B`.
_COMPONENT_PREFIX = {
    (layer, projection): key[: -len(".weight")] for layer, projection, key in extract_deltas.KEYS
}


def component_index():
    """Every addressable rank-1 component of the adapter delta, as ``(layer, projection, j)``.

    DERIVED, never typed. The count is the product of two quantities this repository already
    committed: the 36-key wrap enumeration (``extract_deltas.KEYS``, itself an explicit product of
    ``N_LAYER`` and the six ``TARGET_PROJECTIONS``) and the production rank
    (``LoRAConfig().r``). Writing the product as a literal would let the base grow a layer, or the
    rank move, while a stale constant kept the sweep quietly scanning the wrong surface — the
    "declared invariant silently becomes false" defect this project names as its most recurring.

    Ordered ``(layer, projection, j)`` with ``j`` innermost, following the committed ``KEYS``
    order, so the index is a stable, total ordering that a later tie-break can address by position.
    """
    index = [
        (layer, projection, j)
        for layer, projection, _key in extract_deltas.KEYS
        for j in range(PRODUCTION_RANK)
    ]
    _prove(
        len(index) == len(extract_deltas.KEYS) * PRODUCTION_RANK,
        f"component index holds {len(index)} addresses but the committed wrap set is "
        f"{len(extract_deltas.KEYS)} projections at rank {PRODUCTION_RANK}, i.e. "
        f"{len(extract_deltas.KEYS) * PRODUCTION_RANK} rank-1 components — the surgery surface "
        "and the artifact it addresses disagree",
    )
    _prove(
        len(set(index)) == len(index),
        "component index holds duplicate addresses — a component counted twice would make the "
        "ablation prefix length k a lie about how much of the delta was removed",
    )
    return index


# Module-scope census: running the derivation at import is what makes the proofs above fire on any
# import of this pin, not only when something happens to call the function.
N_COMPONENTS = len(component_index())


def ablate_components(adapter, components):
    """M1: zero the addressed rank-1 components. Returns a NEW artifact; mutates nothing.

    ``adapter`` is an ``export_adapter``-shaped artifact (``checkpoint.py:196``) — ``adapter`` /
    ``lora_config`` / ``base_fingerprint`` — and NOT the bare tensor dict, because the artifact is
    the object the audits read. ``load_adapter_weights``' scale audit reads
    ``artifact["lora_config"]`` (``inject.py:119-129``), so an operator taking only the tensors
    could not be round-tripped through the audit it has to survive, and a caller re-wrapping the
    tensors by hand each time would be re-declaring ``lora_config`` on every one of the sweep's
    applies. Taking the artifact means every application re-passes the scale audit for free.

    ``scale`` is neither recomputed nor touched here (PITFALLS P3): ``lora_config`` passes through
    by reference, unmodified, so ``alpha`` and ``r`` are byte-identical in the returned artifact.

    BOTH factors are zeroed, never one. The component's contribution is
    ``scale * outer(B[:, j], A[j, :])``; zeroing only ``B[:, j]`` already sends that outer product
    to zero for the CURRENT weights, but it leaves ``A[j, :]`` carrying live values that any later
    write to ``B`` would resurrect, and it makes the erased artifact's own arithmetic depend on
    which half was cleared. Zeroing both makes the component's absence a property of the file.

    The input artifact is never mutated: every tensor is ``detach().clone()``d (the
    ``snapshot_params`` idiom, ``inject.py:64``), so the caller's PRE-erasure adapter survives for
    the paired delta the (b) condition needs.
    """
    _prove(
        "adapter" in adapter and "lora_config" in adapter,
        f"ablate_components expects an export_adapter-shaped artifact with 'adapter' and "
        f"'lora_config' keys; got keys {sorted(adapter)} — a bare lora_ tensor dict cannot carry "
        "the scale the load audit reads",
    )
    rank = adapter["lora_config"]["r"]
    out = dict(adapter)
    out["adapter"] = {k: v.detach().clone() for k, v in adapter["adapter"].items()}

    seen = set()
    for address in components:
        layer, projection, j = address
        _prove(
            address not in seen,
            f"component {address} addressed twice — a duplicate is silently idempotent, which "
            "would make the reported number of ablated components larger than the number of "
            "components actually removed",
        )
        seen.add(address)
        prefix = _COMPONENT_PREFIX.get((layer, projection))
        _prove(
            prefix is not None,
            f"({layer}, {projection}) is not a wrapped projection — the committed wrap set is "
            f"{sorted(_COMPONENT_PREFIX)}",
        )
        _prove(
            0 <= j < rank,
            f"component index j={j} is outside [0, {rank}) for an artifact trained at "
            f"r={rank} — this address does not exist in the artifact being ablated",
        )
        keys = (f"{prefix}.lora_A", f"{prefix}.lora_B")
        missing = [key for key in keys if key not in out["adapter"]]
        _prove(
            not missing,
            f"adapter artifact is missing {missing} for ({layer}, {projection}) — it does not "
            "describe the committed wrap set; refusing to ablate a key set it does not have",
        )
        out["adapter"][keys[1]][:, j] = 0.0  # B[:, j]
        out["adapter"][keys[0]][j, :] = 0.0  # A[j, :]

    return out


if __name__ == "__main__":  # pragma: no cover - self-check, not a test suite
    # Smallest runnable check that fails if the derivation breaks. The census is PRINTED rather
    # than asserted against a literal — `component_index`'s own proof is what pins it.
    print(
        f"[phase19_erasure] mechanism {MECHANISM_ID}, {len(MECHANISM_RULE)} rule clauses committed"
    )
    print(
        f"[phase19_erasure] component index: {len(extract_deltas.KEYS)} wrapped projections x "
        f"rank {PRODUCTION_RANK} = {N_COMPONENTS} addressable rank-1 components"
    )
