"""Phase 41 E1 (ERASE-03..ERASE-10) — erasure across facts, orderings and seeds.

    .venv/bin/python scripts/phase41_erasure.py preflight   # the launch checks, writes nothing
    .venv/bin/python scripts/phase41_erasure.py run         # pending prep units, then the cells
    .venv/bin/python scripts/phase41_erasure.py emit        # CPU: the erasure record
    .venv/bin/python scripts/phase41_erasure.py report      # the markdown from the erasure record

preflight: every launch refusal (clean tree, device, budget, frozen pre-registration), nothing
written. run: the pending prep units, then — once the floors fill file is tracked — the pending
cells, in ``phase41_prereg.UNITS`` order. emit: the erasure record on CPU from the committed
records. report: the markdown rendered from the committed erasure record.

Every rule lives in ``phase41_prereg`` (frozen, read through ``_prereg()``, never restated here).
The pin (``phase19_erasure``) and ``phase18_extraction`` are imported unedited (ERASE-08): the
gradient path is a grad-enabled twin of ``span_nll_from_ids``' forward in this file, checked
against the pin's ``value_span_nll_mean`` at every gradient (D-02).

Torch-free at import only: every torch-importing module and the pre-registration are imported
inside the functions that need them.
"""

import datetime
import gc
import hashlib
import pathlib
import re
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import phase25_run  # noqa: E402  — atomic_write_json (torch-free)
import phase36_ledger  # noqa: E402  (torch-free; the per-unit attempt)

# FIXED: the cwd of every git call and the base of the module digests.
_REPO = pathlib.Path(__file__).resolve().parent.parent
# The default OUTPUT root (results/, data/) and the identity that selects the real-root branches.
_ROOT = _REPO
FRONT = "E1"
LAUNCH_PATHSPEC = ("scripts", "src", "results", "artifacts")
PREREG_FILE = "scripts/phase41_prereg.py"
DRIVER_FILE = "scripts/phase41_erasure.py"
# Not in DISCLOSED_MODULES: it does not exist until plan 41-13 (preflight treats it, plan 41-08).
FLOORS_FILE = "scripts/phase41_floors_prereg.py"
DISCLOSED_MODULES = (DRIVER_FILE, PREREG_FILE)
MODULES = DISCLOSED_MODULES + (
    "scripts/phase19_erasure.py",
    "scripts/phase18_extraction.py",
    "scripts/phase14_recall.py",
    "scripts/teach_persona.py",
    "scripts/phase37_routes.py",
    "scripts/phase40_prereg.py",
    "scripts/phase40_noise.py",
    "scripts/erasure_gate.py",
    "scripts/mitigation_gate.py",
    "scripts/phase35_prereg.py",
    "scripts/phase19_run.py",
    "scripts/phase36_ledger.py",
    "scripts/phase36_caps.py",
    "scripts/phase25_run.py",
    "scripts/phase38_rank.py",
    "scripts/phase39_ctx.py",
    "scripts/phase14_factset.py",
)
RUN_PROVENANCE_KEYS = (
    "git_sha_at_launch",
    "git_sha_at_end",
    "head_moved_during_run",
    "device",
    "torch_version",
    "started_utc",
    "finished_utc",
)
ARM_PREFIX = "phase41"
# Does not match results/phase41_*: a rehearsal file never lands under the record glob.
REHEARSAL_PREFIX = "phase41rh"
# root/"data"/WORK_DIR holds every raw or partial output.
WORK_DIR = "phase41_e1"
# ENTRIES["stop_for_rafael"]: the in-run STOPs; each writes its evidence, then exits.
STOP_KINDS = ("d02_inequality", "control_gap_mismatch", "phase40_adapter_digest")


def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[phase41_erasure] {message}")


def _sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _rel(path, base):
    return pathlib.Path(path).relative_to(base).as_posix()


def module_sha256():
    """``{rel: sha256}`` of MODULES as they are in the repository now (``_REPO``, never the
    patchable output root)."""
    return {rel: _sha256(_REPO / rel) for rel in MODULES}


_prove(set(DISCLOSED_MODULES) <= set(MODULES), "DISCLOSED_MODULES must be a subset of MODULES")


def _import_modules():
    """Import every MODULES file (the driver is the running code) BEFORE preflight takes
    module_sha256(), so no module a record's module_sha256_at_launch names is first read from disk
    hours into the run (Phase 40 WR-04)."""
    import importlib

    for rel in MODULES:
        path = pathlib.PurePosixPath(rel).with_suffix("")
        if rel != DRIVER_FILE:
            importlib.import_module(
                ".".join(path.parts[1:]) if path.parts[0] == "src" else path.name
            )


def _is_real(root):
    """The real root, or any root inside the repository."""
    resolved = pathlib.Path(root).resolve()
    return resolved == pathlib.Path(_ROOT).resolve() or resolved.is_relative_to(_REPO.resolve())


def _root_ledger(root, *paths):
    """The ONE root/ledger pairing; ``paths`` are the explicit ledger (and heartbeat). The real
    root reads and writes the milestone ones only; a tmp root its own explicit ones, never the
    milestone ones (38-REVIEW DR-01). Returns whether ``root`` is real."""
    if _is_real(root):
        _prove(
            all(p is None for p in paths),
            "the real root runs into the milestone ledger and heartbeat; an explicit ledger / "
            "heartbeat is a rehearsal into a tmp root outside the repository",
        )
        return True
    _prove(
        all(p is not None for p in paths),
        "a rehearsal root needs an explicit ledger_path and heartbeat_path (38-REVIEW DR-01)",
    )
    milestone = {
        (phase36_ledger._ROOT / phase36_ledger.LEDGER_PATH).resolve(),
        pathlib.Path(phase36_ledger.HEARTBEAT_PATH).resolve(),
    }
    _prove(
        {pathlib.Path(p).resolve() for p in paths}.isdisjoint(milestone),
        "a rehearsal root writes its own ledger and heartbeat, never the milestone ones "
        "(38-REVIEW DR-01)",
    )
    return False


def _prereg():
    """phase41_prereg, imported lazily (torch at import through phase35_prereg.seed_list)."""
    import phase41_prereg

    return phase41_prereg


def _device():
    from personacore.preflight import preflight_device

    return preflight_device(strict=True)["device"]


def _write_once(path, blob):
    path = pathlib.Path(path)
    _prove(not path.exists(), f"{path} exists: write-once")
    path.parent.mkdir(parents=True, exist_ok=True)
    phase25_run.atomic_write_json(path, blob)


def _release():
    import torch

    gc.collect()
    if torch.backends.mps.is_available():  # never reached on a CPU-only host (ubuntu CI)
        torch.mps.empty_cache()


def stop_for_rafael(unit, kind, evidence, *, root):
    """ENTRIES["stop_for_rafael"]: write the evidence under data/phase41_e1/stops/, then exit.
    Write-once: a second STOP never overwrites the first file."""
    _prove(kind in STOP_KINDS, f"stop kind {kind!r} is not one of {STOP_KINDS}")
    _prove(
        isinstance(unit, str) and re.fullmatch(r"[A-Za-z0-9_.-]+", unit) and unit[0] != ".",
        f"unit {unit!r} is not a plain file-name stem",
    )
    root = pathlib.Path(root)
    utc = _now()
    path = root / "data" / WORK_DIR / "stops" / f"{unit}_{utc.replace(':', '')}.json"
    _write_once(path, {"unit": unit, "kind": kind, "evidence": evidence, "utc": utc})
    raise SystemExit(f"STOP FOR RAFAEL {kind} {unit}: see {_rel(path, root)}")


# =================================================================================================
# The first-order Taylor gradient ordering (D-01..D-05; ERASE-04). The pin is imported unedited.
# =================================================================================================


def lora_modules(model, prefixes):
    """``{(layer, projection): LoRALinear}`` for every prefix (the real call passes the pin's
    ``_COMPONENT_PREFIX``), each proved a LoRALinear."""
    from personacore.lora import LoRALinear

    modules = {key: model.get_submodule(prefix) for key, prefix in prefixes.items()}
    for key, module in modules.items():
        _prove(isinstance(module, LoRALinear), f"{key} -> {prefixes[key]} is not a LoRALinear")
    return modules


def component_gradients(loss_fn, modules):
    """``(loss, {(layer, projection, j): g_j})`` with ``g_j = sum_i B[i, j] dLoss/dB[i, j]``.

    Scaling rank-1 component j by ``s_j`` is replacing B by ``B diag(s)`` (the pin's
    ``scale * outer(B[:, j], A[j, :])``), so ``dLoss/ds_j`` at ``s = 1`` is that sum: no new
    parameter, no model edit. ``torch.autograd.grad`` (not ``backward``) so no parameter's
    ``.grad`` is written; every ``lora_B.requires_grad`` is restored in a finally."""
    import torch

    keys = list(modules)
    flags = [modules[k].lora_B.requires_grad for k in keys]
    try:
        for k in keys:
            modules[k].lora_B.requires_grad_(True)
        with torch.enable_grad():
            loss = loss_fn()
            grads = torch.autograd.grad(loss, [modules[k].lora_B for k in keys])
        g = {}
        for k, grad in zip(keys, grads):
            per_j = (grad * modules[k].lora_B.detach()).sum(dim=0)
            for j in range(per_j.shape[0]):
                g[(*k, j)] = float(per_j[j])
        return float(loss), g
    finally:
        for k, flag in zip(keys, flags):
            modules[k].lora_B.requires_grad_(flag)


def value_span_loss(model, ids, ctx_len, device):
    """The grad-enabled twin of ``phase18_extraction.span_nll_from_ids``' forward, line for line
    (shift, value-span mask from ``ctx_len - 1``, ``ignore_index=-100``, the admissible
    reduction). Returns the loss tensor; D-02 checks it against the pin at every gradient."""
    import phase18_extraction
    import torch
    import torch.nn.functional as F

    _prove(ctx_len >= 1 and len(ids) > ctx_len, "a value span needs a context and a value")
    x = torch.tensor([ids[:-1]], dtype=torch.long, device=device)
    y = torch.tensor([ids[1:]], dtype=torch.long, device=device)
    span = torch.zeros_like(y, dtype=torch.bool)
    span[:, ctx_len - 1 :] = True
    y = y.masked_fill(~span, -100)
    logits, _ = model(x)
    flat_logits = logits.view(-1, logits.size(-1))
    flat_y = y.reshape(-1)
    n_scored = int((flat_y != -100).sum())
    _prove(n_scored == len(ids) - ctx_len, f"the span mask scored {n_scored} targets")
    return F.cross_entropy(
        flat_logits,
        flat_y,
        reduction=phase18_extraction.ADMISSIBLE_NLL_REDUCTION,
        ignore_index=-100,
    )


def value_ids(tok, slot, value):
    """``(ids, ctx_len)`` exactly as ``phase18_extraction.value_span_nll`` builds them under the
    admissible frame."""
    import phase14_factset
    import phase18_extraction

    from personacore.dialogue import ASSISTANT_ID

    preamble = phase18_extraction._frame_preamble(
        phase14_factset.SLOT_FORMS[slot], phase18_extraction.ADMISSIBLE_NLL_FRAME
    )
    context = [ASSISTANT_ID] + list(tok.encode(preamble))
    return context + list(tok.encode(value)), len(context)


def taylor_scores(model, tok, device, *, slot, value, unit, root):
    """D-01 / D-02: the component gradients of the value-span NLL under the current weights, the
    grad value checked against the pin's ``value_span_nll_mean`` (any difference stops for
    Rafael). The base is frozen for the gradient; every ``requires_grad`` is restored."""
    import phase19_erasure

    flags = [(p, p.requires_grad) for p in model.parameters()]
    try:
        model.requires_grad_(False)
        ids, ctx_len = value_ids(tok, slot, value)
        modules = lora_modules(model, phase19_erasure._COMPONENT_PREFIX)
        started = time.perf_counter()
        loss, g = component_gradients(lambda: value_span_loss(model, ids, ctx_len, device), modules)
        forward_backward = time.perf_counter() - started
        started = time.perf_counter()
        nograd = phase19_erasure.value_span_nll_mean(model, tok, device, slot=slot, value=value)
        forward = time.perf_counter() - started
    finally:
        for p, flag in flags:
            p.requires_grad_(flag)
    d02 = _prereg().d02_check(loss, nograd)
    if d02["stop"]:
        stop_for_rafael(unit, "d02_inequality", d02, root=root)
    return {
        "scores": g,
        "d02": d02,
        "forward_seconds": forward,
        "forward_backward_seconds": forward_backward,
    }


def gradient_ordering(load, score, *, index, rerank_at):
    """D-01 / D-03 / D-04 / D-05: the full ordering of ``index``. At each point of ``rerank_at``
    the ordered prefix is loaded and the not-yet-ablated components are ranked by score ascending,
    ties by address (the mirror of ``select_ablation_prefix``'s ``(-contribution, address)``);
    positions past the last point come from the last ranking. Returns every ranking and the wall
    seconds (the D-05 cost)."""
    index = list(index)
    _prove(
        len(rerank_at) >= 1
        and rerank_at[0] == 0
        and all(a < b for a, b in zip(rerank_at, rerank_at[1:]))
        and rerank_at[-1] < len(index),
        f"rerank_at {rerank_at!r} must start at 0, increase strictly and stay below {len(index)}",
    )
    started = time.perf_counter()
    ordered, rankings = [], []
    for i, point in enumerate(rerank_at):
        _prove(point == len(ordered), f"rerank point {point} != prefix length {len(ordered)}")
        load(tuple(ordered))
        s = score()
        done = set(ordered)
        ranking = sorted((a for a in index if a not in done), key=lambda a: (s["scores"][a], a))
        take = rerank_at[i + 1] - point if i + 1 < len(rerank_at) else len(ranking)
        ordered += ranking[:take]
        rankings.append(
            {
                "at": point,
                "scores": [[list(a), s["scores"][a]] for a in ranking],
                "d02": s.get("d02"),
                "forward_seconds": s.get("forward_seconds"),
                "forward_backward_seconds": s.get("forward_backward_seconds"),
            }
        )
    _prove(sorted(ordered) == sorted(index), "the ordering is not a permutation of the index")
    return {
        "ordered": tuple(ordered),
        "rankings": rankings,
        "rerank_at": tuple(rerank_at),
        "seconds": time.perf_counter() - started,
    }


def model_gradient_ordering(
    model, tok, device, artifact, *, slot, value, variant, calibration, unit, root
):
    """The gradient ordering of ``artifact`` on ``model`` at the frozen re-rank points; the
    snapshot-first rule of the pin (``ablate_components(artifact, [])``); the model is left
    loaded with the intact adapter."""
    import phase19_erasure

    from personacore.lora import load_adapter_weights

    snapshot = phase19_erasure.ablate_components(artifact, [])
    try:
        out = gradient_ordering(
            lambda prefix: load_adapter_weights(
                model, phase19_erasure.ablate_components(snapshot, list(prefix))
            ),
            lambda: taylor_scores(model, tok, device, slot=slot, value=value, unit=unit, root=root),
            index=phase19_erasure.component_index(),
            rerank_at=_prereg().rerank_points(variant, calibration=calibration),
        )
    finally:
        load_adapter_weights(model, snapshot)
    return {**out, "variant": variant}
