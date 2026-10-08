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
import pathlib
import re
import shutil
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
    (never results/phase41_*: the floors are filled from it later)."""
    import phase19_erasure as pin  # torch at import: lazy

    prereg = _prereg()
    _prove(ordering in prereg.ORDERINGS, f"ordering {ordering!r} is not one of {prereg.ORDERINGS}")
    _prove(seed in prereg.SEEDS, f"seed {seed!r} is not one of {prereg.SEEDS}")
    root = pathlib.Path(root)
    record = root / "data" / WORK_DIR / f"cal_erased_{ordering}_seed{seed}.json"
    _prove(not record.exists(), f"{record} exists: the cal-erased records are write-once")
    record.parent.mkdir(parents=True, exist_ok=True)
    pin.run_erasure_arm(
        "cal-erased",
        device,
        corpus_path=pin.CALIBRATION_CORPUS_PATH,
        adapter_path=adapter_path,
        components=list(components),
        record_path=record,
    )
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
