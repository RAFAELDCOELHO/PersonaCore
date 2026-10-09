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

import collections.abc
import datetime
import gc
import hashlib
import json
import math
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import phase25_run  # noqa: E402  — atomic_write_json, beat, start_heartbeat (torch-free)
import phase36_caps  # noqa: E402  (torch-free at import; the launch caps)
import phase36_ledger  # noqa: E402  (torch-free; the per-unit attempt)

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402

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


# =================================================================================================
# The calibration (D-10, D-11, D-03; ERASE-06): the ONE training helper and both orderings.
# =================================================================================================


def arm_name(seed, *, rehearsal=False):
    """``e1_calibration_seed<seed>`` (``e1rh_`` for the rehearsal): never Phase 19's
    ``erase_calibration``, never a teach_persona arm."""
    seeds = _prereg().SEEDS
    _prove(seed in seeds, f"seed {seed!r} is not one of {seeds}")
    return f"{'e1rh' if rehearsal else 'e1'}_calibration_seed{seed}"


def arm_paths(seed, *, rehearsal=False):
    """teach_persona's write targets for one calibration arm, under the phase41 / phase41rh
    prefix."""
    import teach_persona as tp  # torch at import: lazy

    prefix = REHEARSAL_PREFIX if rehearsal else ARM_PREFIX
    return tp.arm_outputs(arm_name(seed, rehearsal=rehearsal), prefix=prefix)


def train_calibration_adapter(seed, *, root, rehearsal=False):
    """D-10: one fresh calibration adapter at ``seed``; the driver's ONE call of teach_persona's
    arm trainer (registered in tests/test_phase23_resume.py; no resume_from). The recipe is
    ``phase19_erasure._cmd_cal_train``'s, ``arm_spec("cal_first_person_replay")``; that command is
    never called (it takes no seed and writes Phase 19's paths). The csv moves under
    ``root``/data/phase41_e1/<arm>/ and the emptied results/ directory is removed; the shippable
    persona_adapter.pt is proved byte-unchanged around the call."""
    import phase14_factset
    import phase14_recall as recall  # torch at import: lazy
    import teach_persona as tp  # same

    root = pathlib.Path(root)
    arm = arm_name(seed, rehearsal=rehearsal)
    prefix = REHEARSAL_PREFIX if rehearsal else ARM_PREFIX
    paths = arm_paths(seed, rehearsal=rehearsal)
    csv_dst = root / "data" / WORK_DIR / arm / "run.csv"
    for path in (paths["adapter"], paths["checkpoint"], paths["bin"], paths["mask"], csv_dst):
        _prove(not path.exists(), f"{path} exists: stale output. Move it in a reviewed step")
    facts, second_person, replay_ratio = tp.arm_spec("cal_first_person_replay")
    production = _sha256(recall.ADAPTER_PATH)
    result = tp.train_arm(
        arm,
        facts=facts,
        family_ids=phase14_factset.TAUGHT_FAMILY_IDS,
        second_person=second_person,
        replay_ratio=replay_ratio,
        seed=seed,
        prefix=prefix,
    )
    csv_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(paths["csv"]), str(csv_dst))
    try:
        paths["csv"].parent.rmdir()  # empty after the move
    except OSError as exc:  # IN-02: a stray file never costs the trained seed; dirty checks see it
        print(f"CSV DIR KEPT {paths['csv'].parent}: {exc.strerror}", flush=True)
    _prove(
        _sha256(recall.ADAPTER_PATH) == production,
        f"{recall.ADAPTER_PATH} (persona_adapter.pt) changed during training",
    )
    return {
        "seed": seed,
        "arm": arm,
        "prefix": prefix,
        "adapter": _rel(paths["adapter"], tp._REPO_ROOT),
        "adapter_sha256": _sha256(paths["adapter"]),
        "checkpoint": _rel(paths["checkpoint"], tp._REPO_ROOT),
        "csv": _rel(csv_dst, root),
        "csv_sha256": _sha256(csv_dst),
        "train": {
            k: result[k]
            for k in ("final_train_loss", "ppl_adapter_on", "ppl_adapter_off", "scored_targets")
        },
    }


def calibration_identity(new_adapter):
    """D-11 (descriptive, never an input of the floors): the new calibration adapter against
    Phase 19's, tensor by tensor (``phase40_noise.adapter_identity``, torch.equal). Amendment
    (Rafael 2026-10-08): first the reference file's sha256, at its original path, against the
    digest the prereg reads from ``D11_REFERENCE_RECORD``; a mismatch is a finding, never a
    refusal."""
    import phase19_erasure as pin  # torch at import: lazy
    import phase40_noise
    import teach_persona as tp  # same

    prereg = _prereg()
    reference = tp.arm_outputs(pin.CALIBRATION_ARM, prefix=pin.RETRAIN_PREFIX)["adapter"]
    reference_sha256 = _sha256(reference)
    matches = reference_sha256 == prereg.D11_REFERENCE_SHA256
    return {
        **phase40_noise.adapter_identity(new_adapter, reference),
        "reference": _rel(reference, tp._REPO_ROOT),
        "reference_sha256": reference_sha256,
        "reference_record": prereg.D11_REFERENCE_RECORD,
        "reference_record_sha256": prereg.D11_REFERENCE_SHA256,
        "reference_sha256_matches_record": matches,
        "finding": None
        if matches
        else (
            f"the reference adapter's sha256 {reference_sha256} is not the "
            f"{prereg.D11_REFERENCE_RECORD}::{prereg.D11_REFERENCE_KEY} digest "
            f"{prereg.D11_REFERENCE_SHA256}"
        ),
    }


def twin_references(fact):
    """The calibration twin reference set of ``fact`` (the pin's, siblings removed)."""
    import phase19_erasure as pin  # torch at import: lazy

    return pin.reference_set_for_calibration(fact.slot, fact)


def collateral():
    """``_selected_components``' collateral argument: every core slot's taught value and its
    reference set."""
    import phase14_factset
    import phase18_extraction  # torch at import: lazy

    taught = {f.slot: f.value for f in phase14_factset.LOCKED_FACTS}
    return {
        slot: (taught[slot], phase18_extraction.reference_set_for(slot))
        for slot in phase18_extraction.CORE_SLOTS
    }


def greedy_calibration(model, tok, device, forbid, artifact, fact):
    """D-03: the current ordering on the calibration fact, ``select_ablation_prefix`` with
    ``_selected_components``' argument set (never that function); the applied prefix is
    ``ordered[:k]``."""
    import phase19_erasure as pin  # torch at import: lazy

    out = pin.select_ablation_prefix(
        model,
        tok,
        device,
        artifact,
        slot=fact.slot,
        value=fact.value,
        references=twin_references(fact),
        collateral=collateral(),
        dialogue_ppl=lambda: pin.dialogue_ppl_pair(model, device, forbid),
    )
    return {
        "ordered": out["ordered"],
        "k": out["k"],
        "stopped": out["stopped"],
        "applied": out["ordered"][: out["k"]],
        "curve": out["curve"],
    }


def gradient_calibration(model, tok, device, artifact, fact, *, variant, unit, root):
    """D-03: the gradient ordering on the calibration fact, then the pin's ABLATION_STOP_RULE
    clause (``select_ablation_prefix``' rank scan) with the same twin references: k is the first
    prefix whose rank is not 1, else the whole index. Snapshot first; the model is left intact."""
    import phase19_erasure as pin  # torch at import: lazy

    from personacore.lora import load_adapter_weights

    ordering = model_gradient_ordering(
        model,
        tok,
        device,
        artifact,
        slot=fact.slot,
        value=fact.value,
        variant=variant,
        calibration=True,
        unit=unit,
        root=root,
    )
    ordered = ordering["ordered"]
    snapshot = pin.ablate_components(artifact, [])
    references = twin_references(fact)
    k, stopped = len(pin.component_index()), False
    try:
        for prefix in range(1, k + 1):
            load_adapter_weights(model, pin.ablate_components(snapshot, list(ordered[:prefix])))
            rank, _ = pin._rank_of(
                model, tok, device, slot=fact.slot, value=fact.value, references=references
            )
            if rank != 1:
                k, stopped = prefix, True
                break
    finally:
        load_adapter_weights(model, snapshot)
    return {"ordering": ordering, "k": k, "stopped": stopped, "applied": ordered[:k]}


def cal_erase(ordering, seed, adapter_path, components, *, root, device):
    """D-10: the cal-erased arm over the calibration corpus at the applied prefix, through the
    pin's ``run_erasure_arm``, into the raw write-once record under ``root``/data/phase41_e1/
    (never results/phase41_*: the floors are filled from it later). The pin scores against
    LOCKED_FACTS + SOFT_TIER_FACTS, which hold no calibration fact, so SOFT_TIER_FACTS is extended
    with ``select_calibration_fact()`` for this one call and restored after
    (``phase19_run.cal_score``'s seam; 41-11 rehearsal finding)."""
    import phase14_factset
    import phase19_erasure as pin  # torch at import: lazy

    prereg = _prereg()
    _prove(ordering in prereg.ORDERINGS, f"ordering {ordering!r} is not one of {prereg.ORDERINGS}")
    _prove(seed in prereg.SEEDS, f"seed {seed!r} is not one of {prereg.SEEDS}")
    root = pathlib.Path(root)
    record = root / "data" / WORK_DIR / f"cal_erased_{ordering}_seed{seed}.json"
    _prove(not record.exists(), f"{record} exists: the cal-erased records are write-once")
    record.parent.mkdir(parents=True, exist_ok=True)
    original = phase14_factset.SOFT_TIER_FACTS
    phase14_factset.SOFT_TIER_FACTS = original + (pin.select_calibration_fact(),)
    try:
        pin.run_erasure_arm(
            "cal-erased",
            device,
            corpus_path=pin.CALIBRATION_CORPUS_PATH,
            adapter_path=adapter_path,
            components=list(components),
            record_path=record,
        )
    finally:
        phase14_factset.SOFT_TIER_FACTS = original
    _release()
    return {"record": _rel(record, root), "record_sha256": _sha256(record)}


# =================================================================================================
# The Phase 40 adapters, the control gap (D-13), the cell orderings (ERASE-08), the K = 16 reader
# (D-27), the K = 48 confirmation (D-26), the M1 export and the D-13 wrapper (D-20).
# =================================================================================================


def _noise_floor():
    return json.loads((_REPO / _prereg().NOISE_FLOOR_RECORD).read_text(encoding="utf-8"))


def phase40_adapter(seed, group):
    """ERASE-05: ``{"path", "sha256"}`` of one committed Phase 40 adapter, read from
    ``NOISE_FLOOR_RECORD``::phase41_adapters (the path is repo-relative)."""
    adapters = _noise_floor()["phase41_adapters"]
    _prove(str(seed) in adapters, f"seed {seed!r} is not one of {sorted(adapters)}")
    _prove(
        group in adapters[str(seed)], f"group {group!r} is not one of {sorted(adapters[str(seed)])}"
    )
    return dict(adapters[str(seed)][group])


def measure_control_gap(seed, device):
    """D-13: the dialogue gap re-measured on the intact Phase 40 full adapter before any ablation,
    against the committed ``per_seed[seed].full.dialogue_gap.gap`` (``control_gap_check``; the
    caller stops on ``stop``)."""
    import phase14_recall as recall  # torch at import: lazy
    import phase19_erasure as pin  # same

    model, _cfg, _tok, forbid, _artifact = recall.load_adapted_model(
        device, adapter_path=_REPO / phase40_adapter(seed, "full")["path"]
    )
    pair = pin.dialogue_ppl_pair(model, device, forbid)
    committed = _noise_floor()["per_seed"][str(seed)]["full"]["dialogue_gap"]["gap"]
    gap = pair["adapter_on"] - pair["adapter_off"]
    del model
    _release()
    return {"dialogue_ppl": pair, **_prereg().control_gap_check(gap, committed, device=device)}


def target_fact(target):
    """The one locked fact on slot ``target``."""
    import phase14_factset

    _prove(target in _prereg().TARGETS, f"target {target!r} is not one of {_prereg().TARGETS}")
    facts = [f for f in phase14_factset.LOCKED_FACTS if f.slot == target]
    _prove(len(facts) == 1, f"{len(facts)} locked facts on slot {target!r}")
    return facts[0]


def cell_ordering(model, tok, device, forbid, artifact, *, target, ordering, variant, unit, root):
    """ERASE-08: a cell's ordering. "greedy" is the defect-E route
    ``phase37_routes.select_target_prefix`` (|R| = 8 references; its k, stopped and curve are
    descriptive); the alternative is ``model_gradient_ordering`` at ``variant``."""
    import phase19_erasure as pin  # torch at import: lazy

    prereg = _prereg()
    _prove(ordering in prereg.ORDERINGS, f"ordering {ordering!r} is not one of {prereg.ORDERINGS}")
    fact = target_fact(target)
    if ordering == "greedy":
        import phase37_routes

        out = phase37_routes.select_target_prefix(
            model,
            tok,
            device,
            artifact,
            fact=fact,
            dialogue_ppl=lambda: pin.dialogue_ppl_pair(model, device, forbid),
        )
        return {key: out[key] for key in ("ordered", "k", "stopped", "curve")}
    return model_gradient_ordering(
        model,
        tok,
        device,
        artifact,
        slot=fact.slot,
        value=fact.value,
        variant=variant,
        calibration=False,
        unit=unit,
        root=root,
    )


def k16_read(model, tok, device, forbid, *, target):
    """D-27: K = read_k completions for every A2 corpus entry under the loaded weights, the pin's
    stride (``seed_index * phase18_extraction.K``) after ``seed_everything(recall.SEED)``, the
    clean-room guard in place on the ids dispatched (run_erasure_arm's value set); then the
    target's exposure. The draw dicts are the pin's schema."""
    import phase14_factset
    import phase14_recall as recall  # torch at import: lazy
    import phase18_extraction as x18  # same
    import phase35_prereg
    import teach_persona as tp  # same

    k = _prereg().E1_CHECKPOINT_GRID["read_k"]
    clean_room_values = [
        f.value for f in phase14_factset.LOCKED_FACTS + phase14_factset.SOFT_TIER_FACTS
    ]
    tp.seed_everything(recall.SEED)
    draws = []
    for entry in phase35_prereg.a2_corpus_entries():
        base_ids = x18._guarded_span(entry)
        recall.assert_no_value_in_prompt(
            tok, tok.decode(base_ids), clean_room_values, prompt_ids=base_ids
        )
        realized = entry["realized_injection"]
        completions, stopped = recall.draw_all(
            model,
            tok,
            entry["prompt_ids"],
            device,
            forbid,
            entry["seed_index"] * x18.K,
            n_samples=k - 1,
        )
        _prove(
            len(completions) == k,
            f"{entry['fact_id']!r}/{entry['seed_index']} drew {len(completions)} completions, "
            f"not read_k = {k}",
        )
        draws.append(
            {
                "family": entry["family"],
                "dose": entry["dose"],
                "fact_id": entry["fact_id"],
                "slot": entry["slot"],
                "tier": entry["tier"],
                "arm": x18.ARMS[0],
                "seed_index": entry["seed_index"],
                "prefix_text": tok.decode(entry["prompt_ids"][-realized:]) if realized else None,
                "completions": completions,
                "stopped": stopped,
            }
        )
    exposure = x18.measure_exposure(
        model, tok, device, slot=target, taught_value=target_fact(target).value
    )
    return {"draws": draws, "k": k, "exposure": exposure}


def k48_confirm(target, ordering, seed, checkpoint, components, *, root, device):
    """D-26: the K = confirm_k A2 arm at ``components`` on the seed's Phase 40 full adapter,
    through the pin's ``run_erasure_arm("erased", ...)`` (parity asserted by the pin) into the
    write-once ``root``/``k48_record(...)``; ``target_zero`` from ``record_rows``."""
    import phase19_erasure as pin  # torch at import: lazy

    prereg = _prereg()
    rel = prereg.k48_record(target, ordering, seed, checkpoint)
    record = pathlib.Path(root) / rel
    _prove(not record.exists(), f"{record} exists: the K = 48 records are write-once")
    record.parent.mkdir(parents=True, exist_ok=True)
    pin.run_erasure_arm(
        "erased",
        device,
        adapter_path=_REPO / phase40_adapter(seed, "full")["path"],
        components=list(components),
        record_path=record,
    )
    _release()
    rows = prereg.record_rows(json.loads(record.read_text(encoding="utf-8")))
    return {
        "record": rel,
        "record_sha256": _sha256(record),
        "target_zero": rows[target]["n_answerable"] == 0,
    }


def export_m1(artifact, components, path):
    """D-20: the M1-ablated adapter (``ablate_components``) as a write-once export_adapter file at
    ``path`` (the caller builds it under root/data/phase41_e1/m1/)."""
    import phase19_erasure as pin  # torch at import: lazy

    from personacore.checkpoint import export_adapter

    path = pathlib.Path(path)
    _prove(not path.exists(), f"{path} exists: write-once")
    path.parent.mkdir(parents=True, exist_ok=True)
    ablated = pin.ablate_components(artifact, list(components))
    export_adapter(
        path,
        adapter=ablated["adapter"],
        lora_config=ablated["lora_config"],
        base_fingerprint=ablated["base_fingerprint"],
    )
    return {"path": path, "sha256": _sha256(path)}


def d13_at_stop(m1_path, k48_record_path, device, state):
    """D-20: ``phase40_noise.d13_scores`` on the M1 adapter at the stop, with
    ``phase40_noise.run``'s ruling-c catch: every exception (SystemExit included, never
    KeyboardInterrupt) and every non-conforming return becomes ``d13_not_measured``; the cell is
    never dropped."""
    import phase40_noise
    import phase40_prereg

    try:
        raw = phase40_noise.d13_scores(m1_path, k48_record_path, device, state)
    except (Exception, SystemExit) as exc:
        reason = f"{type(exc).__name__}: {exc}"
        try:
            _release()
        except Exception as cleanup:  # the cleanup may not fail the cell either
            reason += f" (then _release raised {type(cleanup).__name__}: {cleanup})"
        return {**phase40_prereg.d13_not_measured("exception", reason), "n_nlls": None}
    defect = None
    if not isinstance(raw, collections.abc.Mapping) or type(raw.get("measured")) is not bool:
        defect = "no bool 'measured'"
    elif not raw["measured"] and not (
        raw.get("failure_kind") in phase40_prereg.D13_FAILURE_KINDS
        and isinstance(raw.get("reason"), str)
        and raw["reason"].strip()
    ):
        defect = "measured False without a D13_FAILURE_KINDS failure_kind + reason"
    else:
        try:
            json.dumps(raw, sort_keys=True)
        except (TypeError, ValueError) as exc:
            defect = f"not JSON-serialisable ({type(exc).__name__}: {exc})"
    if defect is None:
        return raw
    return {
        **phase40_prereg.d13_not_measured(
            "malformed_reading", f"d13_scores returned a {type(raw).__name__}: {defect}"
        ),
        "n_nlls": None,
    }


# =================================================================================================
# The run inputs and ERASE-05's adapter digests
# =================================================================================================


def run_inputs():
    """Every input file the run reads, from the constants its readers take them from:
    ``refuse_if_dirty`` cannot see the gitignored ones, so a missing one refuses before the ledger
    start line."""
    import phase14_recall as recall  # torch at import: lazy
    import phase19_erasure as pin  # same
    import phase40_prereg
    import teach_persona as tp  # same

    prereg = _prereg()
    adapters = _noise_floor()["phase41_adapters"]
    return (
        tp.CONVBASE_BEST,  # train_arm's base
        tp.TOKENIZER_PATH,
        tp.DIALOG_TRAIN_BIN,  # replay source
        tp.DIALOG_TRAIN_MASK,
        tp.DIALOG_VAL_BIN,  # dialogue PPL
        tp.DIALOG_VAL_MASK,
        recall.CONVBASE_SLIM,  # load_adapted_model
        recall.ADAPTER_PATH,  # the production adapter, proved unchanged around each train
        recall.TOKENIZER_PATH,
        pin.RETENTION_BIN,  # run_erasure_arm's retention perplexity
        pin.PHASE18_CORPUS_PATH,  # run_erasure_arm's corpus
        pin.PHASE18_ARM_RECORD_PATH,  # run_erasure_arm's pre-erasure record
        pin.CALIBRATION_CORPUS_PATH,  # cal_erase's corpus
        tp.arm_outputs(pin.CALIBRATION_ARM, prefix=pin.RETRAIN_PREFIX)["adapter"],  # D-11
        *(_REPO / adapters[str(s)][g]["path"] for s in prereg.SEEDS for g in adapters[str(s)]),
        _REPO / prereg.NOISE_FLOOR_RECORD,
        *(_REPO / phase40_prereg.a2_record(g, s) for s in prereg.SEEDS for g in adapters[str(s)]),
    )


def adapter_digest_failures():
    """ERASE-05: ``[(path, expected, actual)]`` for every Phase 40 adapter of SEEDS whose sha256
    is not the one ``NOISE_FLOOR_RECORD``::phase41_adapters records (actual None: missing)."""
    adapters = _noise_floor()["phase41_adapters"]
    failures = []
    for seed in _prereg().SEEDS:
        for entry in adapters[str(seed)].values():
            path = _REPO / entry["path"]
            actual = _sha256(path) if path.is_file() else None
            if actual != entry["sha256"]:
                failures.append((entry["path"], entry["sha256"], actual))
    return failures


# =================================================================================================
# The rehearsal identity and its disclosure (Phase 40's shape, per unit)
# =================================================================================================

_REQUIRED_IDENTITY_KEYS = frozenset({"git_sha", "module_sha256", "units", "started_utc"})
# The smoke's two keys: absent until the rehearsal's ordering_smoke ran, then both present.
_IDENTITY_KEYS = _REQUIRED_IDENTITY_KEYS | {"cpu_ordering_seconds", "cpu_timings"}


def _load(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def rehearsal_identity_path():
    """The gitignored rehearsal identity under the output root (``_ROOT`` read at call time)."""
    return pathlib.Path(_ROOT) / "data" / "phase41_rehearsal.json"


def _disclosed_digests():
    return {rel: _sha256(_REPO / rel) for rel in DISCLOSED_MODULES}


def _well_formed(identity):
    return (
        isinstance(identity, dict)
        and set(identity) in (_REQUIRED_IDENTITY_KEYS, _IDENTITY_KEYS)
        and isinstance(identity["module_sha256"], dict)
        and set(identity["module_sha256"]) == set(DISCLOSED_MODULES)
        and isinstance(identity["units"], list)
    )


def _kept_identity(path):
    """The identity already at ``path`` (None when absent), refused when malformed or recorded at
    other DISCLOSED_MODULES digests: a changed driver needs a fresh rehearsal (38-REVIEW DR-02)."""
    path = pathlib.Path(path)
    if not path.exists():
        return None
    kept = _load(path)
    _prove(_well_formed(kept), f"{path} is malformed (38-REVIEW DR-03)")
    _prove(
        kept["module_sha256"] == _disclosed_digests(),
        f"{path} was recorded at other {DISCLOSED_MODULES} digests: a changed driver needs a fresh "
        "rehearsal (38-REVIEW DR-02); move the identity aside, never delete it",
    )
    return kept


def record_rehearsal(path, *, units):
    """The FIRST rehearsal attempt's identity, recorded once; a later rehearsal call at the same
    digests appends its units (UNITS order, never removing one) and keeps every other key."""
    path = pathlib.Path(path)
    kept = _kept_identity(path)
    if kept is None:
        identity = {
            "git_sha": git_sha(),
            "module_sha256": _disclosed_digests(),
            "units": [u for u in _prereg().UNITS if u in units],
            "started_utc": _now(),
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        phase25_run.atomic_write_json(path, identity)
        print(f"REHEARSAL RECORDED {identity['git_sha']}", flush=True)
        return {"status": "recorded", **identity}
    grown = [u for u in _prereg().UNITS if u in kept["units"] or u in units]
    if grown != kept["units"]:
        kept = {**kept, "units": grown}
        phase25_run.atomic_write_json(path, kept)
    print(f"REHEARSAL KEPT {kept['git_sha']}", flush=True)
    return {"status": "kept", **kept}


def record_rehearsal_seconds(path, seconds, timings):
    """D-05: the rehearsal smoke's CPU ordering seconds and per-gradient timings, added once to
    the identity; a present value is never overwritten."""
    path = pathlib.Path(path)
    kept = _kept_identity(path)
    _prove(kept is not None, f"the rehearsal identity {path} is missing: record_rehearsal first")
    if "cpu_ordering_seconds" in kept:
        print(f"REHEARSAL SECONDS KEPT {kept['cpu_ordering_seconds']}", flush=True)
        return kept
    identity = {**kept, "cpu_ordering_seconds": seconds, "cpu_timings": list(timings)}
    phase25_run.atomic_write_json(path, identity)
    return identity


def rehearsal_disclosure(identity, *, launch_git_sha, launch_module_sha256):
    """Every commit touching a DISCLOSED_MODULES file between the rehearsal and the launch, its
    subject as the reason, and per-module changed flags (the prereg's on its own)."""
    log = subprocess.run(
        (
            "git",
            "log",
            "--format=%H%x09%s",
            f"{identity['git_sha']}..{launch_git_sha}",
            "--",
            *DISCLOSED_MODULES,
        ),
        cwd=_REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    commits = []
    for line in log.splitlines():
        sha, reason = line.split("\t", 1)
        touched = subprocess.run(
            ("git", "show", "--name-only", "--format=", sha),
            cwd=_REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()
        commits.append(
            {
                "sha": sha,
                "reason": reason,
                "modules": [r for r in DISCLOSED_MODULES if r in touched],
            }
        )
    changed = {
        rel: launch_module_sha256[rel] != identity["module_sha256"][rel]
        for rel in DISCLOSED_MODULES
    }
    driver_changed = any(changed.values())
    _prove(
        not driver_changed or commits,
        "a disclosed module changed after the rehearsal without a commit",
    )
    since = (
        f"{len(commits)} commit(s) touched a disclosed module since"
        if commits
        else "no commit touched a disclosed module since"
    )
    return {
        "statement": (
            f"The CPU rehearsal ran units {', '.join(identity['units'])} on this prereg before "
            f"the MPS run; {since} it."
        ),
        "units_read": identity["units"],
        "rehearsal_git_sha": identity["git_sha"],
        "rehearsal_module_sha256": identity["module_sha256"],
        "launch_git_sha": launch_git_sha,
        "launch_module_sha256": {rel: launch_module_sha256[rel] for rel in DISCLOSED_MODULES},
        "changed": changed,
        "prereg_changed": changed[PREREG_FILE],
        "driver_changed": driver_changed,
        "commits": commits,
    }


# =================================================================================================
# Preflight: every refusal before the first start line
# =================================================================================================

STAGE_1_DONE = "STAGE 1 DONE"


def _variant_path(root):
    return pathlib.Path(root) / "data" / WORK_DIR / "variant.json"


def _tracked_and_clean(*rels):
    """Every repo-relative path tracked by git and unmodified in the working tree."""
    tracked = subprocess.run(
        ("git", "ls-files", "--error-unmatch", "--", *rels), cwd=_REPO, capture_output=True
    )
    if tracked.returncode != 0:
        return False
    status = subprocess.run(
        ("git", "status", "--porcelain", "--", *rels),
        cwd=_REPO,
        capture_output=True,
        text=True,
        check=True,
    )
    return status.stdout == ""


def _stage1_records():
    """The 8 stage-1 records: per prep unit its calibration record and its band record."""
    prereg = _prereg()
    return tuple(
        rel
        for unit in prereg.PREP_UNITS
        for _, o, s in [prereg.unit_key(unit)]
        for rel in (prereg.calibration_record(o, s), prereg.band_record(s, o))
    )


def _unit_records(unit):
    """Every record a unit writes under results/: a prep unit's calibration and band records; a
    cell's record and its K = 16 / K = 48 records at every grid checkpoint (a path that was never
    written is harmless in a pathspec)."""
    prereg = _prereg()
    kind, *key = prereg.unit_key(unit)
    if kind == "prep":
        o, s = key
        return (prereg.calibration_record(o, s), prereg.band_record(s, o))
    grid = prereg.E1_CHECKPOINT_GRID["checkpoints"]
    return (
        prereg.cell_record(*key),
        *(prereg.k16_record(*key, c) for c in grid),
        *(prereg.k48_record(*key, c) for c in grid),
    )


def _launch_pathspec(outcomes):
    """LAUNCH_PATHSPEC plus one ``:(exclude)`` per record of a whole or dropped unit: the run's
    own untracked outputs, nothing else."""
    excluded = [
        rel
        for unit in _prereg().UNITS
        if outcomes.get(unit) in ("whole", "dropped")
        for rel in _unit_records(unit)
    ]
    return LAUNCH_PATHSPEC + tuple(":(exclude)" + rel for rel in excluded)


def _seed_first_prep_unit(seed):
    """ENTRIES["prep_order"]: the seed's first prep unit trains the calibration adapter."""
    prereg = _prereg()
    return next(u for u in prereg.PREP_UNITS if prereg.unit_key(u)[2] == seed)


def _stale_outputs(unit, *, root):
    """Every output a pending unit writes, each of which must not exist before it runs."""
    prereg = _prereg()
    kind, *key = prereg.unit_key(unit)
    paths = [root / rel for rel in _unit_records(unit)]
    if kind == "prep":
        o, s = key
        paths.append(root / "data" / WORK_DIR / f"cal_erased_{o}_seed{s}.json")
        if unit == _seed_first_prep_unit(s):
            rehearsal = not _is_real(root)
            arm = arm_paths(s, rehearsal=rehearsal)
            paths += [arm[k] for k in ("adapter", "checkpoint", "bin", "mask", "csv")]
            paths.append(root / "data" / WORK_DIR / arm_name(s, rehearsal=rehearsal) / "run.csv")
    else:
        paths.append(_ordering_path(root, unit))
        paths += [_m1_path(root, unit, c) for c in prereg.E1_CHECKPOINT_GRID["checkpoints"]]
    return paths


# =================================================================================================
# R-3 b per unit (D-24): a crashed attempt's outputs moved aside (never deleted), its re-run
# =================================================================================================

NOT_PRODUCED = "not produced by the dropped attempt"


def _base(path, root):
    """The root a unit output is listed relative to: ``root``, or teach_persona's repository root
    for a calibration arm path outside it (a rehearsal root)."""
    import teach_persona as tp  # torch at import: lazy

    return root if pathlib.Path(path).is_relative_to(root) else tp._REPO_ROOT


def _output_roots(unit, *, root):
    """``[(base, path)]``: every file or directory a crashed attempt of ``unit`` can leave: its
    stale outputs, each one's atomic-write temp, and for the seed's FIRST prep unit (its training
    unit) the trainer's csv directory and the moved csv's directory. A seed's second prep unit
    never owns the adapter: the first unit's calibration record cites it."""
    prereg = _prereg()
    root = pathlib.Path(root)
    record = root / prereg.unit_record(unit)  # present: drop_attempt refuses; its temp is listed
    paths = [p for p in _stale_outputs(unit, root=root) if p != record]
    kind, *key = prereg.unit_key(unit)
    if kind == "prep" and unit == _seed_first_prep_unit(key[1]):
        rehearsal = not _is_real(root)
        paths += [
            arm_paths(key[1], rehearsal=rehearsal)["csv"].parent,
            root / "data" / WORK_DIR / arm_name(key[1], rehearsal=rehearsal),
        ]
    paths += [
        tmp
        for path in [*paths, record]
        if path.parent.is_dir()
        for tmp in sorted(path.parent.glob(f".{path.name}.*.tmp"))
    ]
    return [(_base(path, root), path) for path in paths]


def partial_outputs(unit, *, root):
    """R-3 b (c): sorted ``(rel, path)`` of every existing file a crashed attempt of ``unit`` left
    (``rel`` relative to the root it lives under)."""
    found = {}
    for base, path in _output_roots(unit, root=root):
        files = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
        found.update((_rel(f, base), f) for f in files)
    return sorted(found.items())


def _latest_dropped_dir(lines, unit, *, what):
    prereg = _prereg()
    _prove(
        prereg.unit_outcomes(lines, (unit,))[unit] == "dropped",
        f"R-3 b: {unit}: only a crashed attempt (closed by a lost line) is {what}, never a whole "
        "or not-run unit",
    )
    utc = prereg.lost_attempts(lines, unit)[-1]
    return utc, prereg.dropped_attempt_dir(unit, utc)


def drop_attempt(
    unit,
    *,
    cause_note,
    approved,
    head_at_dropped_attempt,
    head_change_declared=None,
    root=None,
    ledger_path=None,
):
    """R-3 b: move the latest crashed attempt's partial outputs under
    ``phase41_prereg.dropped_attempt_dir`` (never deleted; emptied directories stay) and write
    its write-once manifest. Run by Claude with ``.venv/bin/python -c`` only after Rafael's
    approved; never from run or main."""
    root = pathlib.Path(root) if root is not None else pathlib.Path(_ROOT)
    _root_ledger(root, ledger_path)
    prereg = _prereg()
    lines = phase36_ledger.read_ledger(ledger_path)
    _prove(
        prereg.run_id(unit) not in phase36_ledger.open_runs(lines),
        f"{unit} has an open attempt: phase36_ledger.py reconcile first",
    )
    lost_utc, rel_dir = _latest_dropped_dir(lines, unit, what="dropped")
    _prove(
        not (root / prereg.unit_record(unit)).exists(),
        f"crash rule (i): {prereg.unit_record(unit)} exists; append its end line, never drop it",
    )
    _prove(not (root / rel_dir).exists(), f"{root / rel_dir} exists: write-once")
    relaunch = git_sha()
    _prove(relaunch != "unknown", "git_sha() could not read HEAD (run from the repo root)")
    outputs = partial_outputs(unit, root=root)
    manifest = {
        "unit": unit,
        "run_id": prereg.run_id(unit),
        "lost_utc": lost_utc,
        "cause_note": cause_note,
        "approved": approved,
        "head_at_dropped_attempt": head_at_dropped_attempt,
        "relaunch_git_sha": relaunch,
        "head_change_declared": head_change_declared,
        "kept": [
            {"from": rel, "path": f"{rel_dir}/{rel}", "sha256": _sha256(path)}
            for rel, path in outputs
        ],
    }
    failures = prereg.dropped_manifest_failures(manifest, unit=unit, lost_utc=lost_utc)
    _prove(not failures, f"R-3 b: the manifest fails: {'; '.join(failures)}")
    for (_, path), item in zip(outputs, manifest["kept"]):
        new = root / item["path"]
        new.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(new))
        _prove(_sha256(new) == item["sha256"], f"{new} changed in the move")
    _write_once(root / rel_dir / prereg.DROPPED_MANIFEST, manifest)
    print(f"DROPPED {unit} {rel_dir} kept={len(manifest['kept'])}", flush=True)
    return manifest


def declare_relaunch(unit, *, head_change_declared, approved, root=None, ledger_path=None):
    """R-3 b (b): declare a HEAD that moved after drop_attempt, only on Rafael's approved naming
    the move; write-once in the latest dropped attempt's directory."""
    root = pathlib.Path(root) if root is not None else pathlib.Path(_ROOT)
    _root_ledger(root, ledger_path)
    prereg = _prereg()
    lines = phase36_ledger.read_ledger(ledger_path)
    _utc, rel_dir = _latest_dropped_dir(lines, unit, what="re-launched")
    path = root / rel_dir / prereg.DROPPED_MANIFEST
    _prove(path.exists(), f"R-3 b: {unit} has no manifest {path}: drop_attempt never ran")
    manifest = _load(path)
    launch = git_sha()
    declaration = {
        "launch_git_sha": launch,
        "head_change_declared": head_change_declared,
        "approved": approved,
    }
    failures = prereg.relaunch_declaration_failures(
        declaration, relaunch_git_sha=manifest["relaunch_git_sha"]
    )
    _prove(not failures, f"R-3 b: the declaration fails: {'; '.join(failures)}")
    _write_once(root / rel_dir / prereg.relaunch_declaration_name(launch), declaration)
    print(f"DECLARED {unit} {launch}", flush=True)
    return declaration


def rerun_units(lines, outcomes, *, root):
    """R-3 b: the dropped units a relaunch re-runs: those whose LATEST lost attempt has a
    drop_attempt manifest on disk that passes ``dropped_manifest_failures`` (Rafael's approved).
    Without one a dropped unit is not pending."""
    prereg = _prereg()
    root = pathlib.Path(root)
    rerun = set()
    for unit, outcome in outcomes.items():
        if outcome != "dropped":
            continue
        utc = prereg.lost_attempts(lines, unit)[-1]
        path = root / prereg.dropped_attempt_dir(unit, utc) / prereg.DROPPED_MANIFEST
        if path.exists() and not prereg.dropped_manifest_failures(
            _load(path), unit=unit, lost_utc=utc
        ):
            rerun.add(unit)
    return frozenset(rerun)


def _dropped_attempts(unit, lines, *, root, launch_git_sha):
    """R-3 b, for a re-run unit: every lost attempt's manifest (oldest first) proved whole, every
    kept file's sha256, every relaunch declaration; the launch HEAD checked on the latest only."""
    prereg = _prereg()
    utcs = prereg.lost_attempts(lines, unit)
    attempts = []
    for utc in utcs:
        rel_dir = prereg.dropped_attempt_dir(unit, utc)
        rel = f"{rel_dir}/{prereg.DROPPED_MANIFEST}"
        _prove(
            (root / rel).exists(),
            f"R-3 b: {unit}'s dropped attempt {utc} has no manifest {rel}: every lost attempt of "
            "a re-run unit is listed",
        )
        manifest = _load(root / rel)
        failures = prereg.dropped_manifest_failures(manifest, unit=unit, lost_utc=utc)
        _prove(not failures, f"R-3 b: {rel} fails: {'; '.join(failures)}")
        for item in manifest["kept"]:
            kept = root / item["path"]
            _prove(
                kept.is_file() and _sha256(kept) == item["sha256"],
                f"R-3 b: kept file {item['path']} is missing or its sha256 differs from {rel}'s",
            )
        declarations = []
        for path in sorted((root / rel_dir).glob(prereg.relaunch_declaration_name("*"))):
            declaration = _load(path)
            failures = prereg.relaunch_declaration_failures(
                declaration, relaunch_git_sha=manifest["relaunch_git_sha"]
            )
            _prove(not failures, f"R-3 b: {path} fails: {'; '.join(failures)}")
            declarations.append({**declaration, "path": _rel(path, root), "sha256": _sha256(path)})
        if utc == utcs[-1]:
            own = root / rel_dir / prereg.relaunch_declaration_name(launch_git_sha)
            failures = prereg.latest_head_failures(
                manifest, _load(own) if own.exists() else None, launch_git_sha=launch_git_sha
            )
            _prove(
                not failures,
                f"R-3 b: HEAD moved after drop_attempt ({manifest['relaunch_git_sha']} -> "
                f"{launch_git_sha}): STOP — take it to Rafael; only on his approved "
                f"phase41_erasure.declare_relaunch, never a relaunch otherwise "
                f"({'; '.join(failures)})",
            )
        attempts.append(
            {
                **manifest,
                "manifest": rel,
                "manifest_sha256": _sha256(root / rel),
                "relaunch_declarations": declarations,
            }
        )
    return attempts


def _compared_attempts(unit, attempts, *, root):
    """R-3 b (d): each dropped attempt of a re-run unit against this attempt's output: the
    calibration adapter tensor by tensor (prep, ``phase40_noise.adapter_identity``) or the cell
    ordering's equality (cell); NOT_PRODUCED when the dropped attempt left none."""
    import phase40_noise

    prereg = _prereg()
    root = pathlib.Path(root)
    kind, *key = prereg.unit_key(unit)
    if kind == "prep":
        new, field = arm_paths(key[1], rehearsal=not _is_real(root))["adapter"], "adapter_identity"
    else:
        new, field = _ordering_path(root, unit), "ordering_equal"
    rel = _rel(new, _base(new, root))
    compared = []
    for attempt in attempts:
        item = next((i for i in attempt["kept"] if i["from"] == rel), None)
        if item is None:
            value = NOT_PRODUCED
        elif kind == "prep":
            value = phase40_noise.adapter_identity(new, root / item["path"])
        else:
            value = (
                _load(root / item["path"])["ordering"]["ordered"]
                == _load(new)["ordering"]["ordered"]
            )
        compared.append({**attempt, field: value})
    return compared


def preflight(*, root=None, ledger_path=None, heartbeat_path=None, device=None, units=None):
    """Every refusal before the first ledger start line (ERASE-05 digests, D-22 stages, D-24,
    D-26). Writes nothing."""
    prereg = _prereg()
    root = pathlib.Path(root) if root is not None else pathlib.Path(_ROOT)
    real = _root_ledger(root, ledger_path, heartbeat_path)
    device = _device() if device is None else device
    if real:
        _prove(device == "mps", f"E1 runs on MPS on the real root; resolved {device!r}")
    else:
        _prove(device == "cpu", f"a rehearsal runs on CPU: pass device='cpu', not {device!r}")
    launch_git_sha = git_sha()
    _prove(launch_git_sha != "unknown", "git_sha() could not read HEAD (run from the repo root)")
    _import_modules()
    launch_modules = module_sha256()
    for path in run_inputs():
        _prove(
            pathlib.Path(path).exists(),
            f"{path} is missing: the run reads it, so this refuses before the ledger start line",
        )
    failures = adapter_digest_failures()
    _prove(
        not failures,
        "ERASE-05: a Phase 40 adapter is not the one "
        f"{prereg.NOISE_FLOOR_RECORD}::phase41_adapters records: "
        + "; ".join(f"{p} sha256 {a} != {e}" for p, e, a in failures),
    )
    lines = phase36_ledger.read_ledger(ledger_path)
    still = set(phase36_ledger.open_runs(lines)) & {prereg.run_id(u) for u in prereg.UNITS}
    for unit in prereg.UNITS:  # a reconcile here would make a finished unit unrecoverable
        _prove(
            prereg.run_id(unit) not in still or not (root / prereg.unit_record(unit)).exists(),
            f"{prereg.run_id(unit)} is open and {prereg.unit_record(unit)} exists: append its end "
            "line by command, NEVER reconcile (a lost line makes this finished unit unrecoverable)",
        )
    _prove(
        not still,
        f"the ledger holds an open attempt for {', '.join(sorted(still))} with no unit record: "
        "once the run is dead, phase36_ledger.py reconcile first",
    )
    outcomes = prereg.unit_outcomes(lines, prereg.UNITS)
    rerun = rerun_units(lines, outcomes, root=root)
    pending = prereg.pending_units(outcomes, rerun)
    prep = tuple(u for u in pending if u in prereg.PREP_UNITS)
    if prep:
        stage = 1
    else:
        not_whole = [u for u in prereg.PREP_UNITS if outcomes[u] != "whole"]
        _prove(
            not not_whole,
            f"prep units {not_whole} are dropped and not re-run: the floors and bands need every "
            "(ordering, seed) (D-22); Rafael rules on each (R-3 b) before any cell",
        )
        if real and not _tracked_and_clean(FLOORS_FILE, *_stage1_records()):
            print(STAGE_1_DONE, flush=True)
            return {"stage": STAGE_1_DONE, "pending": ()}
        stage = 2
    pending = prep if stage == 1 else tuple(u for u in pending if u in prereg.CELL_UNITS)
    if units is not None:
        units = tuple(units)
        _prove(
            units and units == tuple(u for u in pending if u in units),
            f"units {units!r} must be a non-empty subset of the pending stage-{stage} units "
            f"{pending}, in UNITS order",
        )
        pending = units
    _prove(pending, f"nothing to run at stage {stage}: {outcomes}")
    for unit in pending:
        if unit in prereg.PREP_UNITS:
            first = _seed_first_prep_unit(prereg.unit_key(unit)[2])
            _prove(
                outcomes[first] == "whole" or first in pending,
                f"{unit} reuses the adapter its seed's first prep unit {first} trains "
                f"({outcomes[first]}): run that first prep unit first (ENTRIES['prep_order'])",
            )
    refuse_if_dirty(
        who="phase41_erasure",
        detail=(
            "every unit record publishes git_sha and hashes its modules from the working tree; a "
            "run launched from a dirty tree names a commit it cannot be regenerated from"
        ),
        pathspec=_launch_pathspec(outcomes) if real else LAUNCH_PATHSPEC,
        cwd=_REPO,
    )
    for unit in pending:
        for path in _stale_outputs(unit, root=root):
            _prove(not path.exists(), f"{path} exists: an output of pending unit {unit}")
    dropped_attempts = {
        unit: _dropped_attempts(unit, lines, root=root, launch_git_sha=launch_git_sha)
        for unit in pending
        if unit in rerun
    }
    gate = phase36_ledger.require_launch(FRONT, ledger_path=ledger_path)
    # D-26: the K = 48 confirmations are not a binding cap; never passed.
    phase36_caps.check_unit_caps(
        FRONT,
        cells=len(prereg.CELL_UNITS),
        checkpoints_per_cell=len(prereg.E1_CHECKPOINT_GRID["checkpoints"]),
        calibrations=len(prereg.PREP_UNITS),
    )
    if real:
        path = rehearsal_identity_path()
        _prove(
            path.exists(), f"the rehearsal identity {path} is missing: run the CPU rehearsal first"
        )
        identity = _load(path)
        _prove(
            _well_formed(identity) and set(identity) == _IDENTITY_KEYS,
            f"{path} is malformed or lacks cpu_ordering_seconds / cpu_timings: the rehearsal's "
            "ordering_smoke has not run (D-05)",
        )
        _prove(
            identity["module_sha256"][PREREG_FILE] == launch_modules[PREREG_FILE],
            f"{PREREG_FILE} changed after the rehearsal: the prereg is frozen",
        )
        disclosure = rehearsal_disclosure(
            identity, launch_git_sha=launch_git_sha, launch_module_sha256=launch_modules
        )
    else:
        disclosure = {"this_is_the_rehearsal": True}
    variant = _load(_variant_path(root))["variant"] if _variant_path(root).exists() else "unset"
    print(
        f"PREFLIGHT OK {launch_git_sha} device={device} stage={stage} "
        f"pending={','.join(pending)} variant={variant} "
        f"spent_E1_h={gate['spent_seconds'][FRONT] / 3600:.4f}",
        flush=True,
    )
    return {
        "root": root,
        "stage": stage,
        "pending": pending,
        "outcomes": outcomes,
        "launch_git_sha": launch_git_sha,
        "launch_modules": launch_modules,
        "device": device,
        "gate": gate,
        "variant": variant,
        "rehearsal_disclosure": disclosure,
        "dropped_attempts": dropped_attempts,
    }


# =================================================================================================
# The D-02 / D-05 launch-gate smoke: the alternative ordering's variant, fixed before any gradient
# calibration (ENTRIES["alternative_variant"], ["d02_equality"]).
# =================================================================================================


def _variant_record(root):
    path = _variant_path(root)
    _prove(
        path.exists(),
        f"{path} is missing: the D-05 smoke fixes the variant before any gradient calibration",
    )
    return _load(path)


def _variant(root):
    """The frozen variant of the alternative ordering, as the smoke wrote it."""
    return _variant_record(root)["variant"]


def ordering_smoke(*, root, device, cpu_seconds, unit, identity_path):
    """D-02 / D-05, the FIRST step of the first prep attempt: the adaptive cell ordering of
    TARGETS[0] on SEEDS[0]'s intact Phase 40 full adapter, every gradient's d02_check inside
    (a difference stops for Rafael before any record); then the variant by the frozen
    ``alternative_variant``, written write-once to variant.json. A rehearsal root (``identity_path``
    required) uses its own CPU seconds for both and records them into the identity it was given;
    the real root (``identity_path`` None) reads ``cpu_seconds`` from the rehearsal (IN-02:
    ``variant_decided_by`` names the measurement that decided)."""
    import phase14_recall as recall  # torch at import: lazy

    prereg = _prereg()
    root = pathlib.Path(root)
    rehearsal = not _is_real(root)
    if rehearsal:
        _prove(identity_path is not None, "a rehearsal root's smoke records into its identity")
    else:
        _prove(identity_path is None, "the real root's smoke reads the rehearsal identity only")
    path = _variant_path(root)
    _prove(not path.exists(), f"{path} exists: write-once (the variant is fixed once)")
    seed, target = prereg.SEEDS[0], prereg.TARGETS[0]
    model, _cfg, tok, _forbid, artifact = recall.load_adapted_model(
        device, adapter_path=_REPO / phase40_adapter(seed, "full")["path"]
    )
    ordering = model_gradient_ordering(
        model,
        tok,
        device,
        artifact,
        slot=target,
        value=target_fact(target).value,
        variant=prereg.ADAPTIVE,
        calibration=False,
        unit=unit,
        root=root,
    )
    del model
    _release()
    seconds = ordering["seconds"]
    timings = [
        {
            "at": r["at"],
            "forward_seconds": r["forward_seconds"],
            "forward_backward_seconds": r["forward_backward_seconds"],
            "ratio": r["forward_backward_seconds"] / r["forward_seconds"],
        }
        for r in ordering["rankings"]
    ]
    if rehearsal:
        cpu_seconds = seconds
        record_rehearsal_seconds(identity_path, seconds, timings)
    blob = {
        "variant": prereg.alternative_variant(cpu_seconds, seconds),
        "variant_decided_by": (
            "cpu_rehearsal"
            if rehearsal or not prereg.ordering_cost_fits(cpu_seconds)
            else "mps_smoke"
        ),
        "cpu_seconds": cpu_seconds,
        "mps_seconds": seconds,
        "d02": [r["d02"] for r in ordering["rankings"]],
        "timings": timings,
        "rehearsal": rehearsal,
        "ordering_bound": prereg.ENTRIES["e1_unit_prices"]["value"]["e1_ordering_seconds"],
    }
    _write_once(path, blob)
    print(
        f"VARIANT {blob['variant']} decided_by={blob['variant_decided_by']} "
        f"cpu_s={cpu_seconds:.2f} mps_s={seconds:.2f}",
        flush=True,
    )
    return blob


# =================================================================================================
# Stage 1: one ledger attempt per prep unit (D-22, ENTRIES["prep_order"], ["record_layout"])
# =================================================================================================


def _run_provenance(pf, started_utc):
    import torch

    end_sha = git_sha()
    return {
        "git_sha_at_launch": pf["launch_git_sha"],
        "git_sha_at_end": end_sha,
        "head_moved_during_run": end_sha != pf["launch_git_sha"],
        "device": pf["device"],
        "torch_version": torch.__version__,
        "started_utc": started_utc,
        "finished_utc": _now(),
    }


def run_prep_unit(unit, *, pf, started_utc, state, smoke, cpu_seconds, identity_path):
    """One prep unit inside its ledger attempt: [the smoke], the D-13 control gap on the intact
    full adapter (a mismatch on mps stops for Rafael), the band record, the seed's calibration
    adapter (trained by its first prep unit, digest-checked by the second), D-11, the calibration
    ordering on ``select_calibration_fact()``, cal-erased, then the calibration record. Returns
    the calibration record's path (the end line names it)."""
    import phase14_recall as recall  # torch at import: lazy
    import phase19_erasure as pin  # same
    import teach_persona as tp  # same

    prereg = _prereg()
    kind, ordering, seed = prereg.unit_key(unit)
    _prove(kind == "prep", f"{unit} is not a prep unit")
    root, device = pf["root"], pf["device"]
    rehearsal = not _is_real(root)
    if smoke:
        state.update(stage="smoke")
        ordering_smoke(
            root=root,
            device=device,
            cpu_seconds=cpu_seconds,
            unit=unit,
            identity_path=identity_path,
        )
    state.update(stage="control_gap")
    gap = measure_control_gap(seed, device)
    if gap["stop"]:
        stop_for_rafael(unit, "control_gap_mismatch", gap, root=root)
    _write_once(
        root / prereg.band_record(seed, ordering),
        {
            "front": FRONT,
            "phase": 41,
            "unit": unit,
            "seed": seed,
            "ordering": ordering,
            "control_gap": gap["measured"],
            "committed_gap": gap["committed"],
            "equal": gap["equal"],
            "device": device,
            "rehearsal": rehearsal,
            "dialogue_ppl": gap["dialogue_ppl"],
            "rehearsal_disclosure": pf["rehearsal_disclosure"],
            "provenance": {
                "measurement": {"utc": _now(), "device": device, "git_sha": pf["launch_git_sha"]}
            },
        },
    )
    state.update(stage="calibration_adapter")
    adapter = arm_paths(seed, rehearsal=rehearsal)["adapter"]
    first = _seed_first_prep_unit(seed)
    if unit == first:
        training = train_calibration_adapter(seed, root=root, rehearsal=rehearsal)
        adapter_sha256 = training["adapter_sha256"]
    else:
        training = None
        trained = _load(root / prereg.unit_record(first))["adapter"]
        adapter_sha256 = _sha256(adapter)
        _prove(
            adapter_sha256 == trained["sha256"],
            f"{adapter} sha256 {adapter_sha256} is not the one {prereg.unit_record(first)} "
            f"recorded ({trained['sha256']}): the seed's calibration adapter changed between its "
            "prep units (ENTRIES['prep_order'])",
        )
    identity = calibration_identity(adapter)
    state.update(stage="calibration")
    model, _cfg, tok, forbid, artifact = recall.load_adapted_model(device, adapter_path=adapter)
    fact = pin.select_calibration_fact()
    variant = decided_by = None
    started = time.perf_counter()
    if ordering == "greedy":
        cal = greedy_calibration(model, tok, device, forbid, artifact, fact)
        full, d06, detail = cal["ordered"], cal["ordered"], {"curve": cal["curve"]}
    else:
        chosen = _variant_record(root)
        variant, decided_by = chosen["variant"], chosen["variant_decided_by"]
        cal = gradient_calibration(
            model, tok, device, artifact, fact, variant=variant, unit=unit, root=root
        )
        detail = cal["ordering"]
        full = detail["ordered"]
        d06 = [address for address, _ in detail["rankings"][0]["scores"]]
    ordering_seconds = time.perf_counter() - started
    del model
    _release()
    _prove(
        sorted(map(tuple, full)) == sorted(pin.component_index()),
        f"{unit}: the applied ordering is not a full permutation of the component index (D-04)",
    )
    _prove(list(cal["applied"]) == list(full[: cal["k"]]), f"{unit}: applied is not ordered[:k]")
    state.update(stage="cal_erase")
    erased = cal_erase(ordering, seed, adapter, cal["applied"], root=root, device=device)
    rel = prereg.calibration_record(ordering, seed)
    _write_once(
        root / rel,
        {
            "front": FRONT,
            "phase": 41,
            "unit": unit,
            "run_id": prereg.run_id(unit),
            "ordering": ordering,
            "seed": seed,
            "family": "A2",
            "corpus": prereg.CALIBRATION_CORPUS,
            "fact_id": fact.id,
            "draws": _load(root / erased["record"])["draws"],
            "applied_ordering": [list(a) for a in full],
            "k": cal["k"],
            "stopped": cal["stopped"],
            "ordering_detail": detail,
            "ordering_seconds": ordering_seconds,
            "d06_order": [list(a) for a in d06],
            "variant": variant,
            "variant_decided_by": decided_by,
            "adapter": {"path": _rel(adapter, tp._REPO_ROOT), "sha256": adapter_sha256},
            "training": training,
            "d11_identity": identity,
            "cal_erased_record": {"path": erased["record"], "sha256": erased["record_sha256"]},
            "rehearsal": rehearsal,
            "rehearsal_disclosure": pf["rehearsal_disclosure"],
            "dropped_attempts": _compared_attempts(
                unit, pf["dropped_attempts"].get(unit, []), root=root
            ),
            "provenance": {
                "run": _run_provenance(pf, started_utc),
                "module_sha256_at_launch": pf["launch_modules"],
            },
        },
    )
    return rel


# =================================================================================================
# Stage 2: one cell (ERASE-07, D-09, D-20, D-26, D-27) — the pre-registered grid read in order, the
# stop proved equal to Phase 35's e1_stop on the same readings.
# =================================================================================================


def _ordering_path(root, unit):
    """D-04 / D-24: where a cell's full ordering is written before its first read."""
    return pathlib.Path(root) / "data" / WORK_DIR / "orderings" / f"{unit}.json"


def _m1_path(root, unit, checkpoint):
    """D-20: the M1-ablated adapter of a pet_name cell at its stop."""
    return pathlib.Path(root) / "data" / WORK_DIR / "m1" / f"{unit}_k{checkpoint:03d}_adapter.pt"


def run_cell(unit, *, root, device, state):
    """One cell inside its ledger attempt: the seed's intact Phase 40 full adapter, the cell's
    ordering (written write-once before any read), then per GRID checkpoint in order ordering[:c]
    ablated, the K = read_k read and its write-once record, the K = confirm_k confirmation exactly
    when the target's pooled count is 0, and ``driver_stop`` after each checkpoint (any non-None
    value stops). The stop is proved equal to ``phase35_prereg.e1_stop``; a judged pet_name stop
    exports M1 and scores D-13 (a failure is recorded, the cell stays whole). Returns the cell
    blob; run() writes the cell record."""
    import phase14_recall as recall  # torch at import: lazy
    import phase19_erasure as pin  # same
    import phase35_prereg

    from personacore.lora import load_adapter_weights

    prereg = _prereg()
    kind, target, ordering, seed = prereg.unit_key(unit)
    _prove(kind == "cell", f"{unit} is not a cell")
    root = pathlib.Path(root)
    grid = prereg.E1_CHECKPOINT_GRID
    adapter = phase40_adapter(seed, "full")
    model, _cfg, tok, forbid, artifact = recall.load_adapted_model(
        device, adapter_path=_REPO / adapter["path"]
    )
    snapshot = pin.ablate_components(artifact, [])
    variant = None if ordering == "greedy" else _variant(root)
    state.update(stage="ordering")
    started = time.perf_counter()
    detail = cell_ordering(
        model,
        tok,
        device,
        forbid,
        snapshot,
        target=target,
        ordering=ordering,
        variant=variant,
        unit=unit,
        root=root,
    )
    ordering_seconds = time.perf_counter() - started
    ordered = tuple(tuple(a) for a in detail["ordered"])
    _prove(
        sorted(ordered) == sorted(pin.component_index()),
        f"{unit}: the ordering is not a full permutation of the component index (D-04)",
    )
    applied = json.loads(json.dumps(detail))
    _write_once(
        _ordering_path(root, unit),
        {
            "unit": unit,
            "variant": variant,
            "ordering": applied,
            "ordering_seconds": ordering_seconds,
        },
    )
    reads, rows, confirmations, stop = [], [], [], None
    for checkpoint in grid["checkpoints"]:
        state.update(stage=f"k16_{checkpoint}")
        components = list(ordered[:checkpoint])
        load_adapter_weights(model, pin.ablate_components(snapshot, components))
        k16 = k16_read(model, tok, device, forbid, target=target)
        n, q = prereg.k16_target_count(k16["draws"], target)
        rel16 = prereg.k16_record(target, ordering, seed, checkpoint)
        _write_once(
            root / rel16,
            {
                "unit": unit,
                "checkpoint": checkpoint,
                "components": [list(a) for a in components],
                "k": k16["k"],
                "draws": k16["draws"],
                "exposure": k16["exposure"],
                "target_count": [n, q],
                "slot_counts": prereg.k16_slot_counts(k16["draws"]),
                "device": device,
            },
        )
        k16_zero, k48 = n == 0, None
        if k16_zero:
            state.update(stage=f"k48_{checkpoint}")
            started_utc, began = _now(), time.perf_counter()
            k48 = k48_confirm(
                target, ordering, seed, checkpoint, components, root=root, device=device
            )
            seconds = time.perf_counter() - began
            confirmations.append(
                {
                    "checkpoint": checkpoint,
                    "k48_zero": k48["target_zero"],
                    "record": k48["record"],
                    "started_utc": started_utc,
                    "finished_utc": _now(),
                    "seconds": seconds,
                }
            )
        k48_zero = None if k48 is None else k48["target_zero"]
        reads.append((checkpoint, k16_zero, k48_zero))
        rows.append(
            {
                "checkpoint": checkpoint,
                "k16_zero": k16_zero,
                "k48_zero": k48_zero,
                "target_count": [n, q],
                "rank": k16["exposure"]["rank"],  # ERASE-10: recorded, never read by the stop
                "k16_record": rel16,
                "k16_sha256": _sha256(root / rel16),
                "k48_record": None if k48 is None else k48["record"],
                "k48_sha256": None if k48 is None else k48["record_sha256"],
            }
        )
        stop = prereg.driver_stop(reads)
        if stop is not None:
            break
    del model
    _release()
    e1 = phase35_prereg.e1_stop(grid=grid, readings=prereg.stop_readings(reads))
    _prove(
        e1["stop"] == stop, f"{unit}: the driver's stop {stop!r} is not e1_stop's {e1['stop']!r}"
    )
    failures = prereg.confirmation_failures(confirmations, reads)
    _prove(not failures, f"{unit}: the K = confirm_k confirmations fail: {failures}")
    m1 = d13 = None
    if e1["judged"] and target == pin.TARGET_SLOT:
        state.update(stage="d13")
        exported = export_m1(snapshot, list(ordered[:stop]), _m1_path(root, unit, stop))
        m1 = {"path": _rel(exported["path"], root), "sha256": exported["sha256"]}
        d13 = d13_at_stop(
            exported["path"], root / prereg.k48_record(target, ordering, seed, stop), device, state
        )
        if not d13["measured"]:
            print(f"D13 NOT_MEASURED {unit} {d13['failure_kind']}: {d13['reason']}", flush=True)
    print(f"CELL {unit} stop={stop} confirmations={len(confirmations)}", flush=True)
    return {
        "unit": unit,
        "target": target,
        "ordering": ordering,
        "seed": seed,
        "variant": variant,
        "adapter": adapter,
        "applied_ordering": applied,
        "ordering_record": _rel(_ordering_path(root, unit), root),
        "ordering_seconds": ordering_seconds,
        "reads": rows,
        "confirmations": confirmations,
        "confirmation_hours": prereg.confirmation_hours(confirmations),
        "stop": stop,
        "judged": e1["judged"],
        "e1_stop": dict(e1),
        "not_reached_sentence": None if e1["judged"] else prereg.not_reached_sentence(),
        "m1": m1,
        "d13": d13,
    }


def write_cell(unit, *, pf, started_utc, state):
    """run_cell inside its attempt, then the cell record write-once (provenance.run, the rehearsal
    disclosure). Returns the record's path (the end line names it)."""
    prereg = _prereg()
    root = pf["root"]
    blob = run_cell(unit, root=root, device=pf["device"], state=state)
    rel = prereg.unit_record(unit)
    _write_once(
        root / rel,
        {
            "front": FRONT,
            "phase": 41,
            "run_id": prereg.run_id(unit),
            **blob,
            "rehearsal": not _is_real(root),
            "rehearsal_disclosure": pf["rehearsal_disclosure"],
            "dropped_attempts": _compared_attempts(
                unit, pf["dropped_attempts"].get(unit, []), root=root
            ),
            "provenance": {
                "run": _run_provenance(pf, started_utc),
                "module_sha256_at_launch": pf["launch_modules"],
            },
        },
    )
    return rel


# =================================================================================================
# The D-23 pause before every cell and its resume declaration (ENTRIES["e1_pause"],
# ["resume_declaration"])
# =================================================================================================


def _pause_notices(root):
    """Every pause notice written, oldest first (the utc is in the name)."""
    return sorted((pathlib.Path(root) / "data" / WORK_DIR).glob("pause_*.json"))


def _resume_declarations(root):
    """D-23: every resume declaration under root/RESUME_ROOT that holds against a written pause
    notice's e1_hours (``resume_declaration_failures``); e1_pause_due reads only these."""
    prereg = _prereg()
    hours = [_load(path)["e1_hours"] for path in _pause_notices(root)]
    held = []
    for path in sorted((pathlib.Path(root) / prereg.RESUME_ROOT).glob("resume_*.json")):
        declaration = _load(path)
        if any(
            not prereg.resume_declaration_failures(declaration, e1_hours_at_pause=h) for h in hours
        ):
            held.append(declaration)
    return held


def declare_resume(cells, *, approved, e1_hours_at_pause, root=None):
    """D-23: Rafael's resume declaration answering the latest pause notice, written write-once as
    the next free resume_<n>.json only when ``resume_declaration_failures`` is []. Run by Claude
    with ``.venv/bin/python -c`` only on his approved; never from run or main."""
    prereg = _prereg()
    root = pathlib.Path(root) if root is not None else pathlib.Path(_ROOT)
    notices = _pause_notices(root)
    _prove(notices, "D-23: no pause notice: a resume declaration answers a pause")
    declaration = {
        "e1_hours_at_pause": e1_hours_at_pause,
        "cells": list(cells),
        "approved": approved,
    }
    failures = prereg.resume_declaration_failures(
        declaration, e1_hours_at_pause=_load(notices[-1])["e1_hours"]
    )
    _prove(not failures, f"D-23: the resume declaration fails: {'; '.join(failures)}")
    n = 1
    while (root / prereg.resume_declaration_name(n)).exists():
        n += 1
    path = root / prereg.resume_declaration_name(n)
    _write_once(path, declaration)
    print(f"RESUME DECLARED {_rel(path, root)} cells={','.join(cells)}", flush=True)
    return declaration


def _pause(unit, *, root, ledger_path):
    """D-23 before a cell's require_launch, between attempts only (spent refuses while one is
    open): when ``e1_pause_due``, the pause notice written write-once and its path returned;
    else None."""
    prereg = _prereg()
    totals = phase36_ledger.spent(ledger_path=ledger_path)
    if not prereg.e1_pause_due(
        totals["by_front"][FRONT], cell=unit, declarations=_resume_declarations(root)
    ):
        return None
    notice = prereg.pause_notice(
        by_front_seconds=totals["by_front"],
        total_seconds=totals["total_seconds"],
        outcomes=prereg.unit_outcomes(phase36_ledger.read_ledger(ledger_path), prereg.UNITS),
    )
    path = pathlib.Path(root) / "data" / WORK_DIR / f"pause_{_now().replace(':', '')}.json"
    _write_once(path, {**notice, "next_cell": unit})
    print(
        f"PAUSE e1_h={notice['e1_hours']:.4f} next={unit} notice={_rel(path, root)}: take it to "
        "Rafael; only his approved resume declaration (declare_resume) lifts it",
        flush=True,
    )
    return path


# =================================================================================================
# The run: one ledger attempt per unit (D-22, D-24)
# =================================================================================================


def run(
    *,
    root=None,
    ledger_path=None,
    heartbeat_path=None,
    device=None,
    units=None,
    rehearsal_identity=None,
):
    """THE run: preflight, then per pending unit require_launch, ONE start line, the unit, its
    record, the end line naming it. Stage 1 runs the pending prep units (the first one starts
    with the D-02 / D-05 smoke while variant.json is absent) and stops; stage 2 runs the pending
    cells (run_cell). A crash or a STOP inside a unit leaves an open start (reconcile -> lost)."""
    prereg = _prereg()
    root = pathlib.Path(root) if root is not None else pathlib.Path(_ROOT)
    pf = preflight(
        root=root,
        ledger_path=ledger_path,
        heartbeat_path=heartbeat_path,
        device=device,
        units=units,
    )
    if pf["stage"] == STAGE_1_DONE:
        return {"stage": STAGE_1_DONE, "whole": []}
    heartbeat_path = heartbeat_path or phase36_ledger.HEARTBEAT_PATH
    rehearsal = not _is_real(root)
    if rehearsal:  # 38-REVIEW DR-02: refused BEFORE the first start line
        _prove(
            rehearsal_identity is not None,
            "a rehearsal root records its identity: pass rehearsal_identity (a tmp path)",
        )
        _kept_identity(rehearsal_identity)
        cpu_seconds = None
    else:
        _prove(rehearsal_identity is None, "the real root records no rehearsal identity")
        cpu_seconds = _load(rehearsal_identity_path())["cpu_ordering_seconds"]
    whole = []
    for i, unit in enumerate(pf["pending"]):
        if unit in prereg.CELL_UNITS and _pause(unit, root=root, ledger_path=ledger_path):
            return {"stage": pf["stage"], "whole": whole, "paused": unit}
        phase36_ledger.require_launch(FRONT, ledger_path=ledger_path)
        rid = prereg.run_id(unit)
        phase36_ledger.append("start", run_id=rid, phase=41, front=FRONT, ledger_path=ledger_path)
        if rehearsal and i == 0:  # after the first start line, before the first measurement
            record_rehearsal(rehearsal_identity, units=pf["pending"])
        state = {"point": rid, "stage": "start", "shape": None, "draw_index": None}
        # B1: the thread's first beat waits a full period: beat once now.
        phase25_run.beat(heartbeat_path, **state)
        stop, thread = phase25_run.start_heartbeat(heartbeat_path, state)
        started_utc = _now()
        try:
            if unit in prereg.CELL_UNITS:
                record = write_cell(unit, pf=pf, started_utc=started_utc, state=state)
            else:
                record = run_prep_unit(
                    unit,
                    pf=pf,
                    started_utc=started_utc,
                    state=state,
                    smoke=unit == prereg.PREP_UNITS[0] and not _variant_path(root).exists(),
                    cpu_seconds=cpu_seconds,
                    identity_path=rehearsal_identity,
                )
            state.update(stage="done")
        finally:
            stop.set()
            thread.join()
        phase36_ledger.append(
            "end", run_id=rid, phase=41, front=FRONT, record=record, ledger_path=ledger_path
        )
        print(f"UNIT {unit} WHOLE", flush=True)
        whole.append(unit)
    outcomes = prereg.unit_outcomes(phase36_ledger.read_ledger(ledger_path), prereg.PREP_UNITS)
    if pf["stage"] == 1 and all(v == "whole" for v in outcomes.values()):
        print(STAGE_1_DONE, flush=True)
    print(f"RUN DONE whole={whole}", flush=True)
    return {"stage": pf["stage"], "whole": whole}


# =================================================================================================
# The emit (CPU): the erasure record from the committed records, every verdict and reading through
# the frozen pre-registration (D-15..D-21, D-26..D-28; ERASE-06, ERASE-09, ERASE-10)
# =================================================================================================


def _key(*parts):
    """A JSON key for a tuple key: its parts joined by ``|``."""
    return "|".join(str(p) for p in parts)


# IN-01 (a), Rafael 2026-10-09: the CPU rehearsal's own records are scratch / gitignored; the
# committed lines that quote its erasure record's D-02 reading are these (cited, never re-typed).
D02_CPU_REHEARSAL_RECORD = {
    "path": ".planning/phases/41-erasure-across-facts-orderings-and-seeds/41-11-SUMMARY.md",
    "lines": (172, 176),
    "commit": "2098294",
}
_DROPPED_SUMMARY_KEYS = (
    "lost_utc",
    "cause_note",
    "manifest",
    "manifest_sha256",
    "relaunch_git_sha",
    "head_change_declared",
    "ordering_equal",
    "adapter_identity",
)


def _dropped_summary(attempts):
    """WR-02 (emit only): per dropped attempt of a re-run unit, as its sha-pinned unit record
    lists it: the manifest's fields, the kept-file count and the comparison with the re-run."""
    return [
        {k: a[k] for k in _DROPPED_SUMMARY_KEYS if k in a} | {"n_kept": len(a["kept"])}
        for a in attempts
    ]


def build_record(root, *, ledger_path=None, floors=None, bands=None):
    """The erasure record from the records alone: per cell condition_a / condition_b (pre = the
    seed's intact Phase 40 full A2 record) / condition_c / cell_verdict on the stop's K = 48
    record, NOT_RUN for a cell never whole; the pair labels, summary_counts, the 4 x 2 x 2 table
    and every declared descriptive reading. ``floors`` / ``bands`` default (real root only) to the
    floors fill file's two fills, imported here. Every input record is proved by the sha256 its
    producer named and listed with its sha256 in ``inputs``."""
    import phase19_erasure as pin  # torch at import: lazy
    import phase35_prereg
    import phase37_routes  # torch at import: lazy
    import phase38_prereg
    import phase40_prereg

    prereg = _prereg()
    greedy = prereg.ORDERINGS[0]
    root = pathlib.Path(root)
    inputs = {}
    if floors is None or bands is None:
        _prove(
            _is_real(root),
            "a rehearsal root passes floors and bands (the two fills on its own stage-1 records); "
            "the floors fill file is the real root's",
        )
        import phase41_floors_prereg

        floors = phase41_floors_prereg.E1_CONDITION_A_FLOORS if floors is None else floors
        bands = phase41_floors_prereg.E1_CONDITION_C_BAND_INPUTS if bands is None else bands
        inputs[FLOORS_FILE] = _sha256(root / FLOORS_FILE)  # IN-05 (ii)

    def read(base, rel, sha256=None):
        path = pathlib.Path(base) / rel
        digest = _sha256(path)
        _prove(sha256 is None or digest == sha256, f"{rel}'s sha256 differs from its producer's")
        inputs[rel] = digest
        return _load(path)

    lines = phase36_ledger.read_ledger(ledger_path)
    outcomes = prereg.unit_outcomes(lines, prereg.UNITS)
    not_whole = [u for u in prereg.PREP_UNITS if outcomes[u] != "whole"]
    _prove(not not_whole, f"prep units {not_whole} are not whole: no floor or band without them")

    cal = {}
    for unit in prereg.PREP_UNITS:
        _, o, s = prereg.unit_key(unit)
        cal[(o, s)] = read(root, prereg.calibration_record(o, s))
        read(root, prereg.band_record(s, o))
    chosen = {(r["variant"], r["variant_decided_by"]) for (o, _), r in cal.items() if o != greedy}
    _prove(len(chosen) == 1, f"the gradient calibration records disagree on the variant: {chosen}")
    ((variant, decided_by),) = chosen
    variant_path = _variant_path(root)
    variant_content = _variant_record(root)  # IN-05 (i): gitignored, so copied into the record
    _prove(
        (variant_content["variant"], variant_content["variant_decided_by"])
        == (variant, decided_by),
        f"{variant_path} disagrees with the gradient calibration records ({variant}, {decided_by})",
    )

    noise = read(_REPO, prereg.NOISE_FLOOR_RECORD)
    a2 = {
        (g, s): read(_REPO, phase40_prereg.a2_record(g, s))
        for g in phase40_prereg.GROUPS
        for s in phase40_prereg.SEEDS
    }
    rows40 = {key: prereg.record_rows(rec) for key, rec in a2.items()}
    ranges = prereg.slot_ranges(noise, {s: rows40[("full", s)] for s in phase40_prereg.SEEDS})
    labels = prereg.varies_labels(ranges)
    retention_rel, retention = prereg.retention_floor_record()
    inputs[retention_rel] = _sha256(_REPO / retention_rel)
    d13_ranges = prereg.d13_ranges(noise)

    cells, verdicts, d13 = {}, {}, {}
    for unit in prereg.CELL_UNITS:
        _, t, o, s = prereg.unit_key(unit)
        block = {"unit": unit, "target": t, "ordering": o, "seed": s, "outcome": outcomes[unit]}
        no_m2 = (
            None
            if t == pin.TARGET_SLOT
            else prereg.m1_m2_rows(t, full_rows=None, m1_rows=None, m2_rows=None, noise_floor=noise)
        )
        if outcomes[unit] != "whole":
            cells[unit] = {**block, "verdict": prereg.NOT_RUN, "m1_m2": no_m2, "d13": None}
            verdicts[(t, o, s)] = prereg.NOT_RUN
            if t == pin.TARGET_SLOT:
                d13[(o, s)] = prereg.d13_comparison({"measured": False}, d13_ranges)
            continue
        rel = prereg.cell_record(t, o, s)
        rec = read(root, rel)
        reads = []
        for row in rec["reads"]:
            k16 = read(root, row["k16_record"], row["k16_sha256"])
            if row["k48_record"] is not None:
                inputs[row["k48_record"]] = _sha256(root / row["k48_record"])
                _prove(
                    inputs[row["k48_record"]] == row["k48_sha256"],
                    f"{row['k48_record']}'s sha256 differs from {rel}'s",
                )
            reads.append(
                {
                    **{k: row[k] for k in ("checkpoint", "k16_zero", "k48_zero", "rank")},
                    "target_count": k16["target_count"],
                    "slot_counts": k16["slot_counts"],
                }
            )
        triples = [(r["checkpoint"], r["k16_zero"], r["k48_zero"]) for r in reads]
        stop = prereg.driver_stop(triples)
        _prove(
            stop == rec["stop"],
            f"{rel}: its reads stop at {stop!r}, the record says {rec['stop']!r}",
        )
        failures = prereg.confirmation_failures(rec["confirmations"], triples)
        _prove(not failures, f"{rel}: the confirmations fail: {failures}")
        block.update(
            record=rel,
            stop=stop,
            reads=reads,
            confirmations=rec["confirmations"],
            confirmation_hours=prereg.confirmation_hours(rec["confirmations"]),
            applied_ordering=rec["applied_ordering"]["ordered"],
            not_reached_sentence=rec["not_reached_sentence"],
            m1=rec["m1"],
            dropped_attempts=_dropped_summary(rec["dropped_attempts"]),
        )
        if stop == phase35_prereg.NOT_REACHED:
            verdict = prereg.cell_verdict(
                stop=stop,
                target_n=None,
                target_q=None,
                zero_results_have_nll=None,
                a=None,
                b=None,
                c=None,
            )
            block.update(verdict, conditions=None, m1_m2=no_m2, d13=None)
            if t == pin.TARGET_SLOT:
                d13[(o, s)] = prereg.d13_comparison({"measured": False}, d13_ranges)
        else:
            k48 = read(root, prereg.k48_record(t, o, s, stop))
            post = prereg.record_rows(k48)
            n, q = post[t]["n_answerable"], post[t]["n_questions"]
            conditions = {
                "a": prereg.condition_a(n, q, floors[(t, o, s)]["floor"]),
                "b": prereg.condition_b(post, rows40[("full", s)], t),
                "c": prereg.condition_c(k48["dialogue_ppl"], tuple(bands[(s, o)])),
            }
            verdict = prereg.cell_verdict(
                stop=stop,
                target_n=n,
                target_q=q,
                zero_results_have_nll=phase37_routes.route_a(k48),
                **conditions,
            )
            pet = t == pin.TARGET_SLOT
            block.update(
                verdict,
                conditions=conditions,
                retention=prereg.retention_rows(
                    k48, a2[("full", s)], a2[("m2", s)] if pet else None, cap=retention["cap"]
                ),
                m1_m2=prereg.m1_m2_rows(
                    t,
                    full_rows=rows40[("full", s)],
                    m1_rows=post,
                    m2_rows=rows40[("m2", s)],
                    noise_floor=noise,
                ),
                nontarget_damage=prereg.nontarget_damage(conditions["b"], labels),
                d13=prereg.d13_comparison(rec["d13"], d13_ranges) if pet else None,
            )
            if pet:
                d13[(o, s)] = block["d13"]
        cells[unit] = block
        verdicts[(t, o, s)] = block["verdict"]

    pairs = {
        (t, o): {s: verdicts[(t, o, s)] for s in prereg.SEEDS}
        for t in prereg.TARGETS
        for o in prereg.ORDERINGS
    }
    d21 = prereg.d21_reading(d13)
    d21 = {**d21, "per_cell": {_key(*k): v for k, v in d21["per_cell"].items()}}
    first = {s: cal[prereg.unit_key(_seed_first_prep_unit(s))[1:]] for s in prereg.SEEDS}
    gradient = [r for (o, _), r in cal.items() if o != greedy]
    devices = {r["provenance"]["run"]["device"] for r in gradient}
    d02 = [x["d02"] for r in gradient for x in r["ordering_detail"]["rankings"]]
    off = read(_REPO, phase38_prereg.ADAPTER_OFF_RECORD)
    if {"attack_family", "k"} <= set(off["config"]):
        basis, readings = "a2_rows", phase40_prereg.a2_rows(off, *phase40_prereg.a2_scope(off))
    else:
        basis, readings = "exposure", phase38_prereg._exposure_rows(off["exposure"])
    prefix = read(_REPO, phase38_prereg.CURVE_RECORD)["ordered_prefix"]
    g1337 = cells[prereg.cell_unit(pin.TARGET_SLOT, greedy, prereg.SEEDS[0])]
    observed = {
        "d11_calibration_identity": first[prereg.SEEDS[0]]["d11_identity"],
        "d21_d13_at_stop": d21["per_cell"],
        "greedy_1337_phase19_prefix": prereg.NOT_RUN
        if "applied_ordering" not in g1337
        else g1337["applied_ordering"][: len(prefix)],
        "d02_cpu_equality": {"devices": sorted(devices), "d02": d02},
    }
    held = {
        "d11_calibration_identity": observed["d11_calibration_identity"]["tensors_identical"],
        "d21_d13_at_stop": d21["prediction_held"],
        "greedy_1337_phase19_prefix": None
        if "applied_ordering" not in g1337
        else observed["greedy_1337_phase19_prefix"] == prefix,
        "d02_cpu_equality": all(x["equal"] for x in d02) if devices == {"cpu"} else None,
    }
    cite = D02_CPU_REHEARSAL_RECORD
    where = f"{cite['path']}:{cite['lines'][0]}-{cite['lines'][1]} (commit {cite['commit']})"
    reasons = {
        "d02_cpu_equality": None
        if devices == {"cpu"}
        else (
            f"D-02 equality on CPU was established in the CPU rehearsal ({where}), and on "
            f"{', '.join(sorted(devices))} it is verified at every gradient of this run; "
            "d02_cpu_equality is None because no gradient of this run runs on CPU"
        )
    }
    spent = phase36_ledger.spent(ledger_path=ledger_path, fronts=(FRONT,))
    prep_ids = {prereg.run_id(u) for u in prereg.PREP_UNITS}
    record = {
        "phase": 41,
        "front": FRONT,
        "status": "COMPLETE"
        if all(outcomes[u] == "whole" for u in prereg.CELL_UNITS)
        else "PARTIAL",
        "outcomes": outcomes,
        "variant": variant,
        "variant_decided_by": decided_by,
        "variant_record": {
            "path": _rel(variant_path, root),
            "sha256": _sha256(variant_path),
            "content": variant_content,
        },
        "cells": cells,
        "pairs": {_key(*k): {**prereg.pair_label(v), "verdicts": v} for k, v in pairs.items()},
        "summary": prereg.summary_counts(pairs),
        "table": {
            t: {o: {s: verdicts[(t, o, s)] for s in prereg.SEEDS} for o in prereg.ORDERINGS}
            for t in prereg.TARGETS
        },
        "calibrations": {
            "d12": prereg.d12_rows(floors),
            "d06": {
                s: prereg.spearman_rho(cal[(greedy, s)]["d06_order"], r["d06_order"])
                for (o, s), r in cal.items()
                if o != greedy
            },
            "d11": {s: first[s]["d11_identity"] for s in prereg.SEEDS},
            "dropped_attempts": {
                u: _dropped_summary(cal[prereg.unit_key(u)[1:]]["dropped_attempts"])
                for u in prereg.PREP_UNITS
            },
            "condition_a": prereg.ENTRIES["condition_a"]["derivation"],
            "prep_hours": math.fsum(r["seconds"] for r in spent["rows"] if r["run_id"] in prep_ids)
            / 3600,
        },
        "bands": {_key(*k): list(v) for k, v in bands.items()},
        "labels": {"varies": sorted(labels), "ranges": ranges},
        "retention_spread": prereg.retention_spread(
            {s: a2[("full", s)] for s in phase40_prereg.SEEDS},
            {s: a2[("m2", s)] for s in phase40_prereg.SEEDS},
            floor=retention["retention_ppl_noise_floor"],
        ),
        "d21": d21,
        "end_point": {
            "record": phase38_prereg.ADAPTER_OFF_RECORD,
            "sha256": inputs[phase38_prereg.ADAPTER_OFF_RECORD],
            "basis": basis,
            "readings": readings,
        },
        "e1_hours": spent["by_front"][FRONT] / 3600,
        "confirmation_hours": math.fsum(
            c["confirmation_hours"] for c in cells.values() if "confirmation_hours" in c
        ),
        "predictions": {
            name: {
                "prediction": text,
                "observed": observed[name],
                "held": held[name],
                "reason": reasons.get(name),
            }
            for name, text in prereg.ENTRIES["predictions"]["value"].items()
        },
        "not_reached_sentence": prereg.not_reached_sentence(),
        "limits": {
            "d18": prereg.ENTRIES["m1_m2"]["value"],
            "d19": prereg.ENTRIES["varies_label"]["value"],
            "d20": prereg.ENTRIES["d13_block"]["value"],
            "summary_line": prereg.ENTRIES["summary_line"]["value"],
        },
        "inputs": inputs,
        "provenance": {
            "emitted_utc": _now(),
            "git_sha": git_sha(),
            "module_sha256": module_sha256(),
        },
    }
    return json.loads(json.dumps(record, default=dict))


def emit(*, root=None, ledger_path=None, floors=None, bands=None):
    """Write results/phase41_erasure.json ONCE (CPU). On the real root: from a clean tree, and only
    when the floors fill file and every record build_record read are tracked and unmodified."""
    root = pathlib.Path(root) if root is not None else pathlib.Path(_ROOT)
    real = _root_ledger(root, ledger_path)
    prereg = _prereg()
    out = root / prereg.ERASURE_RECORD
    _prove(
        not out.exists(),
        f"{out} exists — REFUSING to overwrite it. The erasure record is write-once; a correction "
        "is a dated continuation via scripts/_addendum.py",
    )
    if real:
        refuse_if_dirty(
            who="phase41_erasure",
            detail=(
                "the erasure record publishes git_sha and hashes its modules from the working "
                "tree; a record written from a dirty tree names a commit it cannot be regenerated "
                "from"
            ),
            pathspec=LAUNCH_PATHSPEC,
            cwd=_REPO,
        )
    record = build_record(root, ledger_path=ledger_path, floors=floors, bands=bands)
    if real:
        _prove(
            _tracked_and_clean(FLOORS_FILE, *record["inputs"]),
            f"{FLOORS_FILE} and every record the erasure record reads must be tracked and clean "
            "(the cell and stage-1 records committed under Rafael's approved) before emit",
        )
    _write_once(out, record)
    print(
        f"EMIT {record['status']} "
        + " ".join(f"{label}={record['summary'][label]}" for label in prereg.PAIR_LABELS),
        flush=True,
    )
    return record


# =================================================================================================
# The report: the erasure record rendered, nothing else (every number read from the record)
# =================================================================================================


def _table(header, rows):
    """A GFM table; a pipe inside a cell is escaped, else it would add cells."""

    def line(cells):
        return "| " + " | ".join(str(c).replace("|", "\\|") for c in cells) + " |"

    return [line(header), "|" + "---|" * len(header), *(line(row) for row in rows), ""]


def _counts(pair):
    return f"{pair[0]}/{pair[1]}"


def _dropped_lines(unit, attempts):
    """WR-02: one report line per dropped attempt of a re-run unit (from the record's summary)."""
    out = []
    for a in attempts:
        field = "ordering_equal" if "ordering_equal" in a else "adapter_identity"
        value = a[field]
        if isinstance(value, dict):
            value = f"tensors_identical {value.get('tensors_identical')}"
        out.append(
            f"- {unit}: dropped attempt lost {a['lost_utc']}; cause note: {a['cause_note']}; "
            f"manifest {a['manifest']} (sha256 {a['manifest_sha256']}); {a['n_kept']} kept "
            f"files; relaunched at {a['relaunch_git_sha']} (HEAD change declared: "
            f"{a['head_change_declared']}); {field} {value}."
        )
    return [*out, ""] if out else []


def _cell_section(unit, c, labels):
    """One cell: verdict, D-27 reads and per-fact counts, D-26 confirmations, (a)/(b)/(c), D-14,
    D-18, D-19 and D-20, each from the cell's block."""
    prereg = _prereg()
    out = [f"### {unit}", ""]
    if c["verdict"] == prereg.NOT_RUN:
        return out + [f"Verdict **{c['verdict']}** (ledger outcome: {c['outcome']}).", ""]
    out += [
        f"Verdict **{c['verdict']}** at stop {c['stop']}; failed conditions: "
        f"{', '.join(c['failed']) or 'none'}; non-targets beyond the margin: "
        f"{', '.join(c['beyond']) or 'none'}; INCONCLUSIVE reason: {c['reason'] or 'none'}.",
        "",
        *_dropped_lines(unit, c["dropped_attempts"]),
    ]
    if c["not_reached_sentence"]:
        out += [f"D-09: {c['not_reached_sentence']}.", ""]
    out += [
        "Reads (D-27: K = read_k at every checkpoint; ERASE-10: the exposure rank recorded, never "
        "read by the stop):",
        "",
        *_table(
            ("checkpoint", "target n/q", "rank", "K = read_k zero", "K = confirm_k zero"),
            [
                [
                    r["checkpoint"],
                    _counts(r["target_count"]),
                    r["rank"],
                    r["k16_zero"],
                    r["k48_zero"],
                ]
                for r in c["reads"]
            ],
        ),
        "Per-fact counts at every checkpoint (K = read_k):",
        "",
        *_table(
            ("slot", *(r["checkpoint"] for r in c["reads"])),
            [
                [
                    slot,
                    *(
                        _counts(
                            [r["slot_counts"][slot][k] for k in ("n_answerable", "n_questions")]
                        )
                        for r in c["reads"]
                    ),
                ]
                for slot in c["reads"][0]["slot_counts"]
            ],
        ),
        f"D-26 confirmations ({len(c['confirmations'])}; {c['confirmation_hours']!r} h):",
        "",
        *_table(
            ("checkpoint", "K = confirm_k zero", "seconds", "started", "finished"),
            [
                [
                    x["checkpoint"],
                    x["k48_zero"],
                    repr(x["seconds"]),
                    x["started_utc"],
                    x["finished_utc"],
                ]
                for x in c["confirmations"]
            ],
        ),
    ]
    if c["conditions"] is not None:
        a, b, cc = (c["conditions"][k] for k in ("a", "b", "c"))
        out += [
            f"(a): Wilson upper {a['upper']!r} against the floor {a['floor']!r}: holds "
            f"{a['holds']} (vazia no ponto de parada julgado: o alvo está em 0).",
            "",
            f"(b): every non-target against the same seed's intact full adapter, margin "
            f"{b['margin']!r} compared exactly; holds {b['holds']}:",
            "",
            *_table(
                (
                    "slot",
                    "pre",
                    "post",
                    "delta",
                    "beyond",
                    prereg.VARIES_LABEL,
                    "full min-max",
                    "m2 min-max",
                ),
                [
                    [
                        slot,
                        _counts(row["pre"]),
                        _counts(row["post"]),
                        repr(row["delta"]),
                        row["beyond"],
                        "sim" if slot in labels["varies"] else "não",
                        *(
                            f"{labels['ranges'][slot][g]['min']}-{labels['ranges'][slot][g]['max']}"
                            if g in labels["ranges"][slot]
                            else "—"
                            for g in ("full", "m2")
                        ),
                    ]
                    for slot, row in b["slots"].items()
                ],
            ),
            f"(c): dialogue gap {cc['gap']!r} in [{cc['lo']!r}, {cc['hi']!r}]: "
            f"holds {cc['holds']}.",
            "",
        ]
        damage = c["nontarget_damage"]
        out += [
            f"D-19: beyond the margin, {damage['beyond_labelled']} labelled "
            f'"{prereg.VARIES_LABEL}" ({", ".join(damage["labelled"]) or "none"}) and '
            f"{damage['beyond_unlabelled']} unlabelled "
            f"({', '.join(damage['unlabelled']) or 'none'}); "
            f"(b) would fail on the unlabelled alone: {damage['b_fails_on_unlabelled_alone']}.",
            "",
        ]
        r = c["retention"]
        out += [
            "D-14 retention_ppl (descriptive, no verdict):",
            "",
            *_table(
                ("stop", "intact full", "m2", "v4.0 cap", prereg.V4_CAP_LABEL),
                [
                    [
                        repr(r["stop"]),
                        repr(r["intact_full"]),
                        repr(r["m2"]),
                        repr(r["cap"]),
                        r[prereg.V4_CAP_LABEL],
                    ]
                ],
            ),
        ]
    m1_m2 = c["m1_m2"]
    if m1_m2 is not None and "comparison" in m1_m2:
        out += [f"D-18: {m1_m2['comparison']}.", ""]
    elif m1_m2 is not None:
        out += [
            "D-18 M1 x M2 (descriptive; 'fora da faixa' não é teste estatístico: duas seeds "
            "contra cinco retreinos do M2):",
            "",
            *_table(
                ("slot", "full", "M1", "M2", "M1 - full", "M2 - full", "M2 min-max", "M1"),
                [
                    [
                        slot,
                        _counts(row["full"]),
                        _counts(row["m1"]),
                        _counts(row["m2"]),
                        repr(row["m1_minus_full"]),
                        repr(row["m2_minus_full"]),
                        f"{row['m2_range'][0]}-{row['m2_range'][1]}",
                        row["m1_in_range"],
                    ]
                    for slot, row in m1_m2.items()
                ],
            ),
        ]
    if c["d13"] is not None:
        if c["d13"]["measured"]:
            out += [
                "D-20 D-13 at the stop beside Phase 40's M2 range (descriptive):",
                "",
                *_table(
                    ("reading", "value", "M2 range", "label"),
                    [
                        [name, x["value"], f"{x['range'][0]}-{x['range'][1]}", x["label"]]
                        for name, x in c["d13"]["readings"].items()
                    ],
                ),
            ]
        else:
            out += ["D-20: D-13 not measured at this stop.", ""]
    return out


def render_report(record):
    """The erasure report, rendered from the record only (pure; returns the markdown)."""
    import re as regex

    record = json.loads(json.dumps(record, sort_keys=True))  # one key type: the file's
    prereg = _prereg()
    seeds = [str(s) for s in prereg.SEEDS]
    summary = record["summary"]
    out = ["# Phase 41 — E1: erasure across facts, orderings and seeds", ""]
    out += [
        "## Summary (D-16, D-17)",
        "",
        f"Status: **{record['status']}**. Of the {summary['n_pairs']} (target, ordering) pairs: "
        + ", ".join(f"{label} {summary[label]}" for label in prereg.PAIR_LABELS)
        + ".",
        "",
        f'Inside "{prereg.PAIR_LABELS[2]}", each pair counted once under its seeds\' verdicts '
        f"({' + '.join(seeds)}):",
        "",
        *_table(("verdicts", "pairs"), sorted(summary["inside_nao_replicado"].items())),
        f"The rule: {record['limits']['summary_line']}.",
        "",
        *_table(
            ("pair", "label", "per seed"),
            [
                [key, record["pairs"][key]["label"], record["pairs"][key]["text"]]
                for key in (_key(t, o) for t in prereg.TARGETS for o in prereg.ORDERINGS)
            ],
        ),
        "## The 4 x 2 x 2 table (D-15)",
        "",
        *_table(
            ("target", "ordering", *seeds),
            [
                [t, o, *(record["table"][t][o][s] for s in seeds)]
                for t in prereg.TARGETS
                for o in prereg.ORDERINGS
            ],
        ),
        f'A NOT_REACHED cell reads (D-09): "{record["not_reached_sentence"]}". NOT_RUN: a cell '
        "never started (or dropped and not re-run).",
        "",
        f"Alternative ordering variant: {record['variant']} (decided by "
        f"{record['variant_decided_by']}: cpu_seconds "
        f"{record['variant_record']['content']['cpu_seconds']!r}, mps_seconds "
        f"{record['variant_record']['content']['mps_seconds']!r}; "
        f"{record['variant_record']['path']} sha256 {record['variant_record']['sha256']}; "
        "IN-02).",
        "",
        "## Cells",
        "",
    ]
    labels = record["labels"]
    for unit in prereg.CELL_UNITS:
        out += _cell_section(unit, record["cells"][unit], labels)
    cal = record["calibrations"]
    out += [
        "## (a) floors and the calibrations (D-12, D-06, D-11; WR-01)",
        "",
        "(a) é vazia no ponto de parada julgado: the stop requires the target at 0, so (a) holds "
        f"by construction. The four calibrations ({cal['prep_hours']!r} h measured) feed only "
        f"D-12. The entry: {cal['condition_a']}",
        "",
        *_table(
            (
                "ordering",
                "seed",
                "calibration rate",
                "successes/questions",
                "floor",
                "floor_branch",
            ),
            [
                [
                    r["ordering"],
                    r["seed"],
                    repr(r["calibration_rate"]),
                    f"{r['calibration_successes']}/{r['calibration_questions']}",
                    repr(r["floor"]),
                    r["floor_branch"],
                ]
                for r in cal["d12"]
            ],
        ),
        *_table(
            (
                "seed",
                "D-06 Spearman rho (gradient vs greedy)",
                "D-11 reference sha256 matches record",
                "D-11 tensor-identical",
                "D-11 max abs diff",
                "D-11 finding",
            ),
            [
                [
                    s,
                    repr(cal["d06"][s]),
                    cal["d11"][s].get("reference_sha256_matches_record"),
                    cal["d11"][s].get("tensors_identical"),
                    max(
                        (
                            v
                            for v in (cal["d11"][s].get("max_abs_diff") or {}).values()
                            if v is not None
                        ),
                        default=None,
                    ),
                    cal["d11"][s].get("finding"),
                ]
                for s in seeds
            ],
        ),
        *(
            line
            for unit in prereg.PREP_UNITS
            for line in _dropped_lines(unit, cal["dropped_attempts"][unit])
        ),
        "## (c) bands (D-13)",
        "",
        *_table(
            ("seed|ordering", "lo", "hi"),
            [
                [key, *map(repr, record["bands"][key])]
                for key in (_key(s, o) for s in seeds for o in prereg.ORDERINGS)
            ],
        ),
        "## D-19 / D-28 labels",
        "",
        f'"{prereg.VARIES_LABEL}": {", ".join(labels["varies"]) or "none"} (the label never '
        "discounts a delta nor enters a verdict).",
        "",
        *_table(
            ("slot", "basis", "range"),
            [[slot, row["basis"], repr(row["range"])] for slot, row in labels["ranges"].items()],
        ),
        f"The rule: {record['limits']['d19']}.",
        "",
    ]
    spread = record["retention_spread"]
    out += [
        "## D-14 retention spread",
        "",
        *_table(
            ("group", "min", "max", "range", "n"),
            [
                [
                    g,
                    repr(spread[g]["min"]),
                    repr(spread[g]["max"]),
                    repr(spread[g]["range"]),
                    spread[g]["n"],
                ]
                for g in ("full", "m2")
            ],
        ),
        f"Beside the two-seed retention noise floor {spread['retention_ppl_noise_floor']!r}.",
        "",
        "## D-18 / D-20 / D-21",
        "",
        f'D-18: {record["limits"]["d18"]}. "{prereg.OUTSIDE}" não é teste estatístico (two '
        "seeds against five M2 retrains).",
        "",
        f"D-20: {record['limits']['d20']}.",
        "",
        f"D-21 (descriptive, never a criterion): {record['d21']['prediction']}",
        "",
        *_table(
            ("pet_name cell", "reading"),
            [
                [key, record["d21"]["per_cell"][key]]
                for key in (_key(o, s) for o in prereg.ORDERINGS for s in seeds)
            ],
        ),
        f"Prediction held: {record['d21']['prediction_held']}.",
        "",
        "## Predictions (descriptive; a mismatch is a finding, not a failure)",
        "",
        *_table(
            ("prediction", "held"),
            [[name, x["held"]] for name, x in record["predictions"].items()],
        ),
        *(
            f"{name}: {x['reason']}.\n"
            for name, x in record["predictions"].items()
            if x["reason"] is not None
        ),
    ]
    end = record["end_point"]
    out += [
        "## D-08 end point (cited, never re-measured)",
        "",
        f"{end['record']} (sha256 {end['sha256']}), readings by {end['basis']}:",
        "",
        *_table(
            ("slot", "reading"),
            [[slot, json.dumps(value, sort_keys=True)] for slot, value in end["readings"].items()],
        ),
        "## Hours",
        "",
        f"E1 spent (ledger): {record['e1_hours']!r} h; D-26 confirmations: "
        f"{record['confirmation_hours']!r} h; calibrations: {cal['prep_hours']!r} h.",
        "",
        "## Provenance",
        "",
        f"- emitted {record['provenance']['emitted_utc']} at {record['provenance']['git_sha']}",
        f"- {len(record['inputs'])} input records, each with its sha256 in the erasure record",
        "",
    ]
    return regex.sub(r"\n{3,}", "\n\n", "\n".join(out))


def report(*, root=None):
    """Write results/phase41_erasure_report.md ONCE from the erasure record (on the real root only
    from a tracked, unmodified record)."""
    root = pathlib.Path(root) if root is not None else pathlib.Path(_ROOT)
    prereg = _prereg()
    record_path = root / prereg.ERASURE_RECORD
    _prove(record_path.exists(), f"{record_path} is missing: emit the record first")
    _prove(
        not _is_real(root) or _tracked_and_clean(prereg.ERASURE_RECORD),
        f"{prereg.ERASURE_RECORD} must be committed and unmodified before the report renders it",
    )
    out = root / prereg.REPORT_RECORD
    _prove(
        not out.exists(),
        f"{out} exists — REFUSING to overwrite it. The report is write-once; a correction is a "
        "dated continuation via scripts/_addendum.py",
    )
    out.write_text(render_report(_load(record_path)), encoding="utf-8")
    print(f"REPORT {out}", flush=True)
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    commands = {"preflight": preflight, "run": run, "emit": emit, "report": report}
    if len(argv) != 1 or argv[0] not in commands:
        raise SystemExit(__doc__)
    # git_sha() reads the process cwd: every command runs at the repository root.
    os.chdir(_REPO)
    commands[argv[0]]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
