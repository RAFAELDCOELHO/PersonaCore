"""Phase 38 E5 (RANK-02, RANK-03) — exposure rank at the minted sets, on MPS under the ledger.

    .venv/bin/python scripts/phase38_rank.py preflight   # every refusal, writes nothing
    .venv/bin/python scripts/phase38_rank.py run         # THE run: gate, then one scoring pass
    .venv/bin/python scripts/phase38_rank.py crosscheck  # (plan 38-07) CPU cross-check
    .venv/bin/python scripts/phase38_rank.py emit        # (plan 38-07) the record from the sidecars
    .venv/bin/python scripts/phase38_rank.py report      # (plan 38-07) the report

WHAT E5 MEASURES. For each of the eight locked slots, the taught value's rank among one maximum
minted set (results/phase38_minting.json, sizes from phase38_sizes_prereg.E5_SET_SIZES, D-07/D-31),
read at the nested prefixes of that one set (D-08), under eight readings (D-11/D-16/D-21): the
six erasure prefixes k = 0, 8, 16, 32, 64, 78 of the committed ordered_prefix, M2 (the Phase 19
retrain adapter) and the adapter switched off. M2 and adapter-off are descriptive references only.
Each value is scored ONCE per reading, one `phase19_erasure.value_span_nll_mean` call per value
(never batched), and the rank is computed afterwards by `phase38_prereg.rank_in_prefix`.

THE GATE (D-18). Before any minted value is scored, `run` scores the committed reference_set_for
set of all eight slots under all eight readings and requires `rank_in_prefix` to reproduce every
one of the 64 committed ranks. One mismatch writes status GATE_FAILED and scores nothing minted.

RECONSTRUCTION (D-20). The prefix-k models come only from `phase36_probe.adapted_model` (never
`inject_lora`); preflight proves the persona adapter, the ordered_prefix components and the M2
adapter against their committed SHA-256 digests.

LEDGER DISCIPLINE (D-17, D-23). Every refusal (an existing record or sidecar, an OPEN attempt for
RUN_ID, a dirty tree, an unreadable HEAD, an untracked minting record or sizes file,
`require_launch("E5")` — the committed D-13 stops, no second stop rule — a device other than MPS on
the real root, a missing input, a digest mismatch) runs BEFORE the ledger start line and writes
nothing. After the start line every reading's NLLs land in a write-once sidecar before the next
reading; a crash leaves an open start that `phase36_ledger.reconcile` closes with a lost line.

A partial shape (readings / slots / max_size) and a CPU device exist only for a rehearsal into a
tmp root outside the repository; the real root runs the full READINGS x SLOTS x E5_SET_SIZES shape.

Torch-free at import: phase38_sizes_prereg loads torch through its caps call (38-05), so it and
every torch-importing module are imported inside the functions that need them.
"""

import contextlib
import datetime
import gc
import hashlib
import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import phase25_run  # noqa: E402  — beat, start_heartbeat, atomic_write_json
import phase36_caps  # noqa: E402
import phase36_ledger  # noqa: E402
import phase36_probe  # noqa: E402  — adapted_model, e1_components, silenced (torch-free)
import phase38_prereg as prereg  # noqa: E402

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402

# FIXED: the cwd of every git call, the base of the module digests and of every tracked input.
_REPO = pathlib.Path(__file__).resolve().parent.parent
# The default OUTPUT root (results/, data/) and the identity that selects the real-root branches.
_ROOT = _REPO
FRONT = "E5"
RUN_ID = phase36_ledger.run_id(38, FRONT, "rank")
LAUNCH_PATHSPEC = ("scripts", "src", "results")
SIZES_FILE = "scripts/phase38_sizes_prereg.py"
TRACKED_INPUTS = (prereg.MINTING_RECORD, SIZES_FILE)
MODULES = (
    "scripts/phase14_recall.py",
    "scripts/phase18_extraction.py",
    "scripts/phase19_erasure.py",
    "scripts/phase35_prereg.py",
    "scripts/phase36_caps.py",
    "scripts/phase36_ledger.py",
    "scripts/phase36_probe.py",
    "scripts/phase38_prereg.py",
    SIZES_FILE,
    "scripts/phase38_rank.py",
    "scripts/teach_persona.py",
)
# D-34: the modules that decide what is scored and are NOT frozen before the rehearsal
# (scripts/phase38_prereg.py is frozen by the minting record; the other MODULES are pinned
# instruments). Every commit touching one of them after the rehearsal is disclosed with its reason.
DISCLOSED_MODULES = ("scripts/phase38_rank.py", SIZES_FILE)
if not set(DISCLOSED_MODULES) <= set(MODULES):
    raise SystemExit(f"[phase38_rank] {DISCLOSED_MODULES} is not a subset of MODULES")
RUN_PROVENANCE_KEYS = (
    "git_sha_at_launch",
    "git_sha_at_end",
    "head_moved_during_run",
    "device",
    "torch_version",
    "started_utc",
    "finished_utc",
)


def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[phase38_rank] {message}")


def _sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _json(rel):
    return json.loads((_REPO / rel).read_text(encoding="utf-8"))


def module_sha256():
    """``{rel: sha256}`` of MODULES as they are in the repository now."""
    return {rel: _sha256(_REPO / rel) for rel in MODULES}


def _is_real(root):
    """The real root, or any root inside the repository: full shape and MPS only."""
    resolved = pathlib.Path(root).resolve()
    return resolved == pathlib.Path(_ROOT).resolve() or resolved.is_relative_to(_REPO.resolve())


def run_sidecar(root):
    return pathlib.Path(root) / "data" / "phase38_rank_run.json"


def gate_sidecar(root):
    return pathlib.Path(root) / "data" / "phase38_rank_gate.json"


def nll_sidecar(root, reading):
    _prove(reading in prereg.READINGS, f"{reading!r} is not one of {prereg.READINGS}")
    return pathlib.Path(root) / "data" / f"phase38_rank_nll_{reading}.json"


def cpu_sidecar(root):
    return pathlib.Path(root) / "data" / "phase38_rank_cpu.json"


def outputs(root):
    """The record path, then every sidecar path: all must be absent before a run."""
    return (
        pathlib.Path(root) / prereg.RANK_RECORD,
        run_sidecar(root),
        gate_sidecar(root),
        cpu_sidecar(root),
        *(nll_sidecar(root, reading) for reading in prereg.READINGS),
    )


def rehearsal_identity_path():
    """D-34: the gitignored rehearsal identity under the output root (read at call time)."""
    return pathlib.Path(_ROOT) / "data" / "phase38_rehearsal.json"


def record_rehearsal(path, *, readings, slots, max_size):
    """D-34: the FIRST attempt that passed preflight is THE rehearsal; its identity is never
    overwritten. Reads no sidecar."""
    path = pathlib.Path(path)
    if path.exists():
        kept = _load(path)
        print(f"REHEARSAL KEPT {kept['git_sha']}", flush=True)
        return {"status": "kept", **kept}
    identity = {
        "git_sha": git_sha(),
        "module_sha256": {rel: _sha256(_REPO / rel) for rel in DISCLOSED_MODULES},
        "readings": list(readings),
        "slots": list(slots),
        "max_size": max_size,
        "started_utc": _now(),
    }
    phase25_run.atomic_write_json(path, identity)
    print(f"REHEARSAL RECORDED {identity['git_sha']}", flush=True)
    return {"status": "recorded", **identity}


def rehearsal_disclosure(identity, *, launch_git_sha, launch_module_sha256):
    """D-34: every commit touching a DISCLOSED_MODULES file between the rehearsal and the launch,
    its subject as the reason, and per-module changed flags."""
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
        modules = [rel for rel in DISCLOSED_MODULES if rel in touched]
        commits.append({"sha": sha, "reason": reason, "modules": modules})
    changed = {
        rel: launch_module_sha256[rel] != identity["module_sha256"][rel]
        for rel in DISCLOSED_MODULES
    }
    driver_changed = any(changed.values())
    _prove(
        not driver_changed or commits,
        "a scoring module changed after the rehearsal without a commit (D-34)",
    )
    slice_read = {key: identity[key] for key in ("readings", "slots", "max_size")}
    return {
        "statement": (
            f"The CPU rehearsal (38-07) read {', '.join(slice_read['slots'])} at "
            f"|R| {slice_read['max_size']} under {len(slice_read['readings'])} readings, minted "
            "candidates included, before the driver review and the MPS run (D-34)."
        ),
        "slice_read": slice_read,
        "rehearsal_git_sha": identity["git_sha"],
        "rehearsal_module_sha256": identity["module_sha256"],
        "launch_git_sha": launch_git_sha,
        "launch_module_sha256": {rel: launch_module_sha256[rel] for rel in DISCLOSED_MODULES},
        "changed": changed,
        "driver_changed": driver_changed,
        "commits": commits,
    }


def m2_adapter_path():
    """The M2 (Phase 19 retrain) adapter, from the constants that wrote it."""
    import phase19_erasure
    import teach_persona

    return teach_persona.arm_outputs(
        phase19_erasure.RETRAIN_ARM, prefix=phase19_erasure.RETRAIN_PREFIX
    )["adapter"]


def run_inputs():
    """Every input file the run reads: refused before the start line when missing, because
    `refuse_if_dirty` cannot see the gitignored ones (checkpoints/)."""
    import phase14_recall

    return (
        phase14_recall.CONVBASE_SLIM,
        phase14_recall.ADAPTER_PATH,
        phase14_recall.TOKENIZER_PATH,
        m2_adapter_path(),
        *(
            _REPO / rel
            for rel in (
                prereg.MINTING_RECORD,
                prereg.CURVE_RECORD,
                prereg.ERASED_RECORD,
                prereg.KSTAR_SUMMARY,
                prereg.TARGET_SCORES,
                prereg.RETRAIN_RECORD,
                prereg.RETRAIN_SCORES,
                prereg.ADAPTER_OFF_RECORD,
                prereg.ADAPTER_ON_RECORD,
                prereg.PROBE_E1_RECORD,
            )
        ),
    )


def _device():
    from personacore.preflight import preflight_device

    return preflight_device(strict=True)["device"]


def adapter_digests():
    """The only function that reads a .pt file (tests stub it)."""
    import phase14_recall

    return {
        "persona_adapter": _sha256(phase14_recall.ADAPTER_PATH),
        "m2_adapter": _sha256(m2_adapter_path()),
    }


def reconstruction_checks():
    """D-20: the persona adapter, the ordered_prefix components and the M2 adapter, each against
    its committed SHA-256 digest. Returns the three digests."""
    digests = adapter_digests()
    curve = _json(prereg.CURVE_RECORD)
    components = phase36_probe.e1_components()
    _prove(
        len(components) == len(curve["ordered_prefix"]) == prereg.PREFIXES[-1],
        f"{len(components)} components, {len(curve['ordered_prefix'])} in the curve's "
        f"ordered_prefix, not k = {prereg.PREFIXES[-1]}",
    )
    _prove(
        digests["persona_adapter"] == curve["adapter_in_sha256"],
        f"the persona adapter is not the one {prereg.CURVE_RECORD} was swept on (D-20)",
    )
    components_sha256 = prereg.components_sha256(components)
    _prove(
        components_sha256 == _json(prereg.PROBE_E1_RECORD)["configuration"]["components_sha256"],
        f"the ordered_prefix components are not {prereg.PROBE_E1_RECORD}'s (D-20)",
    )
    _prove(
        digests["m2_adapter"] == _json(prereg.RETRAIN_SCORES)["retrain_scores"]["adapter_sha256"],
        f"the M2 adapter is not the one {prereg.RETRAIN_SCORES} scored (D-20)",
    )
    return {**digests, "components_sha256": components_sha256}


def _taught():
    import phase14_factset

    return {fact.slot: fact.value for fact in phase14_factset.LOCKED_FACTS}


def scoring_plan(*, slots=None, max_size=None):
    """``{slot: {taught, minted, size, sizes}}``: the first size - 1 cleared values (D-31)."""
    import phase38_sizes_prereg as sizes_prereg  # torch through its caps call: lazy

    record = _json(prereg.MINTING_RECORD)
    taught = _taught()
    plan = {}
    for slot in slots or prereg.SLOTS:
        size = sizes_prereg.E5_SET_SIZES[slot]
        if max_size is not None:
            size = min(size, max_size)
        plan[slot] = {
            "taught": taught[slot],
            "minted": record["slots"][slot]["cleared"][: size - 1],
            "size": size,
            "sizes": list(prereg.nested_sizes(size)),
        }
    return plan


@contextlib.contextmanager
def reading_model(reading, device):
    """``(model, tok)`` for one reading; the model is released on exit."""
    import torch

    _prove(reading in prereg.READINGS, f"{reading!r} is not one of {prereg.READINGS}")
    scope = contextlib.nullcontext()
    if reading == "M2":
        import phase14_recall

        model, _cfg, tok, _forbid, _artifact = phase14_recall.load_adapted_model(
            device, adapter_path=m2_adapter_path()
        )
    else:
        k = 0 if reading == "adapter_off" else int(reading[1:])
        _prove(k in prereg.PREFIXES, f"k = {k} is not one of {prereg.PREFIXES}")
        model, tok, _forbid = phase36_probe.adapted_model(device, k)
        if reading == "adapter_off":
            from personacore.lora import adapter_disabled

            scope = adapter_disabled(model)
    try:
        with scope:
            yield model, tok
    finally:
        model = None
        gc.collect()
        if torch.backends.mps.is_available():  # never reached on a CPU-only host (ubuntu CI)
            torch.mps.empty_cache()


def score_values(model, tok, device, slot, values, state):
    """One pinned NLL per value, in order, never batched (the gate is exact)."""
    import phase19_erasure

    state.update(shape=slot)
    nlls = []
    with phase36_probe.silenced():
        for i, value in enumerate(values):
            state.update(draw_index=i)
            nlls.append(
                phase19_erasure.value_span_nll_mean(model, tok, device, slot=slot, value=value)
            )
    return nlls


def gate_reading(reading, nll_by_slot):
    """D-18: one row per slot comparing rank_in_prefix with the committed rank."""
    import phase18_extraction

    taught = _taught()
    committed = prereg.committed_gate_ranks()[reading]
    rows = {}
    for slot, nll in nll_by_slot.items():
        references = phase18_extraction.reference_set_for(slot)
        rank = prereg.rank_in_prefix(
            nll, taught[slot], [r for r in references if r != taught[slot]]
        )
        row = committed[slot]
        rows[slot] = {
            "rank": rank,
            "committed_rank": row["rank"],
            "n_references": len(references),
            "equal": rank == row["rank"] and len(references) == row["n_references"],
            "taught_nll": nll[taught[slot]],
            "committed_nll": row["nll_mean"],
            "abs_nll_diff": (
                None if row["nll_mean"] is None else abs(nll[taught[slot]] - row["nll_mean"])
            ),
        }
    return rows


def preflight(*, root=None, ledger_path=None, device=None, readings=None):
    """Every refusal before the ledger start line (D-17, D-23). Writes nothing."""
    import phase38_sizes_prereg as sizes_prereg  # torch through its caps call: lazy

    root = pathlib.Path(root) if root is not None else _ROOT
    # The two I/O-free checks first (D-21, D-17).
    readings = tuple(readings) if readings is not None else prereg.READINGS
    _prove(
        set(readings) <= set(prereg.READINGS) and len(readings) <= prereg.APPROVED_E5_PREFIXES,
        f"readings {readings} are not within the D-21 approval of "
        f"{prereg.APPROVED_E5_PREFIXES} of {prereg.READINGS}",
    )
    resolved = device or _device()
    _prove(
        resolved == "mps" or not _is_real(root),
        f"E5 runs on MPS on the real root (D-17); resolved {resolved!r}. A CPU device is only for "
        "a rehearsal root outside the repository",
    )
    _prove(
        not _is_real(root) or rehearsal_identity_path().exists(),
        f"{rehearsal_identity_path()} is missing — D-34: run the 38-07 rehearsal first; the "
        "real run launches only after the rehearsal identity is recorded",
    )
    for path in outputs(root):
        _prove(not path.exists(), f"{path} exists: the E5 scoring has already run")
    _prove(
        RUN_ID not in phase36_ledger.open_runs(phase36_ledger.read_ledger(ledger_path)),
        f"the ledger holds an open attempt for {RUN_ID}: end it, or reconcile it once the run is "
        "dead, before a new attempt",
    )
    refuse_if_dirty(
        who="phase38_rank",
        detail=(
            "the E5 record publishes git_sha and hashes its modules from the working tree; a run "
            "launched from a dirty tree names a commit it cannot be regenerated from"
        ),
        pathspec=LAUNCH_PATHSPEC,
        cwd=_REPO,
    )
    launch_sha = git_sha()
    _prove(launch_sha != "unknown", "git_sha() could not read HEAD (run from the repo root)")
    for rel in TRACKED_INPUTS:
        tracked = subprocess.run(
            ("git", "ls-files", "--error-unmatch", rel), cwd=_REPO, capture_output=True, text=True
        )
        _prove(tracked.returncode == 0, f"{rel} is not tracked: it must be committed before E5")
    launch_modules = module_sha256()
    gate = phase36_ledger.require_launch(FRONT, ledger_path=ledger_path)
    committed_cap = phase36_caps.committed_budget()["unit_caps"][FRONT]["prefixes"]
    _prove(
        prereg.COMMITTED_PREFIX_CAP == committed_cap,
        f"the budget's committed E5 prefix cap is {committed_cap}, not "
        f"{prereg.COMMITTED_PREFIX_CAP}: the D-21 deviation must stay visible",
    )
    phase36_caps.check_unit_caps(
        FRONT, **phase36_caps.counts_for("e5_set_sizes", sizes_prereg.E5_SET_SIZES)
    )
    for path in run_inputs():
        _prove(
            pathlib.Path(path).exists(),
            f"{path} is missing: the run reads it, so this refuses before the ledger start line",
        )
    reconstruction = reconstruction_checks()
    print(
        f"PREFLIGHT OK {launch_sha} device={resolved} readings={len(readings)} "
        f"projection_h={prereg.E5_PROJECTION_HOURS} stop_h={prereg.E5_STOP_HOURS} "
        f"spent_E5_s={gate['spent_seconds'][FRONT]}",
        flush=True,
    )
    return {
        "git_sha": launch_sha,
        "module_sha256": launch_modules,
        "device": resolved,
        "gate": gate,
        "reconstruction": reconstruction,
        "readings": readings,
    }


def _write_once(path, blob):
    _prove(not path.exists(), f"{path} exists: the sidecars are write-once")
    path.parent.mkdir(parents=True, exist_ok=True)
    phase25_run.atomic_write_json(path, blob)


def run(
    *,
    root=None,
    ledger_path=None,
    heartbeat_path=None,
    device=None,
    readings=None,
    slots=None,
    max_size=None,
    rehearsal_identity=None,
):
    """THE run: preflight, ledger start, the D-18 gate pass, the scoring pass, sidecars, ledger
    end. No in-run stop timer: the committed stop is checked by require_launch (D-23)."""
    import phase18_extraction
    import torch

    root = pathlib.Path(root) if root is not None else _ROOT
    _prove(
        not _is_real(root)
        or (readings is None and slots is None and max_size is None and rehearsal_identity is None),
        "the real root runs the full READINGS x SLOTS x E5_SET_SIZES shape only and records no "
        "rehearsal; a partial shape is a rehearsal into a tmp root outside the repository",
    )
    pre = preflight(root=root, ledger_path=ledger_path, device=device, readings=readings)
    readings, device = pre["readings"], pre["device"]
    plan = scoring_plan(slots=slots, max_size=max_size)
    phase36_ledger.append("start", run_id=RUN_ID, phase=38, front=FRONT, ledger_path=ledger_path)
    heartbeat_path = heartbeat_path or phase36_ledger.HEARTBEAT_PATH
    state = {"point": RUN_ID, "stage": "gate", "shape": None, "draw_index": None}
    phase25_run.beat(heartbeat_path, **state)  # the thread's first beat waits a full period
    if rehearsal_identity is not None:  # D-34: before the first value is scored
        record_rehearsal(rehearsal_identity, readings=readings, slots=list(plan), max_size=max_size)
    stop, thread = phase25_run.start_heartbeat(heartbeat_path, state)
    started = _now()
    try:
        # D-18: every committed rank is reproduced BEFORE any minted value is scored.
        rows = {}
        for reading in readings:
            state.update(stage=f"gate_{reading}")
            with reading_model(reading, device) as (model, tok):
                nll_by_slot = {}
                for slot in plan:
                    references = phase18_extraction.reference_set_for(slot)
                    nlls = score_values(model, tok, device, slot, references, state)
                    nll_by_slot[slot] = dict(zip(references, nlls))
            rows[reading] = gate_reading(reading, nll_by_slot)
        passed = all(row["equal"] for by_slot in rows.values() for row in by_slot.values())
        _write_once(
            gate_sidecar(root),
            {"run_id": RUN_ID, "readings": list(readings), "rows": rows, "passed": passed},
        )
        scored = []
        if passed:
            for reading in readings:
                state.update(stage=f"score_{reading}")
                by_slot = {}
                with reading_model(reading, device) as (model, tok):
                    for slot, row in plan.items():
                        values = [row["taught"], *row["minted"]]
                        nlls = score_values(model, tok, device, slot, values, state)
                        by_slot[slot] = {
                            "taught": row["taught"],
                            "taught_nll": nlls[0],
                            "minted": row["minted"],
                            "minted_nll": nlls[1:],
                        }
                # Write-once BEFORE the next reading: a crash keeps every reading already scored.
                _write_once(
                    nll_sidecar(root, reading),
                    {"run_id": RUN_ID, "reading": reading, "slots": by_slot},
                )
                scored.append(reading)
        status = "SCORED" if passed else "GATE_FAILED"
        end_sha = git_sha()
        if end_sha != pre["git_sha"]:
            print(f"WARN HEAD moved during the run: {pre['git_sha']} -> {end_sha}", flush=True)
        _write_once(
            run_sidecar(root),
            {
                "run_id": RUN_ID,
                "status": status,
                "readings": list(readings),
                "slots": list(plan),
                "max_size": max_size,
                "sizes": {slot: row["size"] for slot, row in plan.items()},
                "git_sha_at_launch": pre["git_sha"],
                "git_sha_at_end": end_sha,
                "head_moved_during_run": end_sha != pre["git_sha"],
                "module_sha256_at_launch": pre["module_sha256"],
                "device": device,
                "torch_version": torch.__version__,
                "started_utc": started,
                "finished_utc": _now(),
                "reconstruction": pre["reconstruction"],
                "gate_sha256": _sha256(gate_sidecar(root)),
                "nll_sha256": {r: _sha256(nll_sidecar(root, r)) for r in scored},
            },
        )
        state.update(stage="done")
    finally:
        stop.set()
        thread.join()
    phase36_ledger.append(
        "end",
        run_id=RUN_ID,
        phase=38,
        front=FRONT,
        record=prereg.RANK_RECORD,
        ledger_path=ledger_path,
    )
    print(f"RUN {status} — next: crosscheck, then emit", flush=True)
    return status


def curve_for(taught, taught_nll, minted, minted_nll, sizes, *, exclude=()):
    """``{str(size): {size, rank, bits}}`` at each nested size: members = minted[: size - 1]
    without the ``exclude`` indices, effective size = len(members) + 1 (D-31, D-27)."""
    nll = {taught: taught_nll, **dict(zip(minted, minted_nll))}
    excluded = set(exclude)
    curve = {}
    for size in sizes:
        members = [v for i, v in enumerate(minted[: size - 1]) if i not in excluded]
        n = len(members) + 1
        rank = prereg.rank_in_prefix(nll, taught, members)
        curve[str(size)] = {"size": n, "rank": rank, "bits": prereg.exposure_bits(rank, n)}
    return curve


def _load(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def crosscheck(*, root=None, device="cpu"):
    """D-19: re-score every gate set and every scored maximum set on CPU into a write-once CPU
    sidecar. Descriptive only; no ledger line (CPU)."""
    import phase18_extraction
    import torch

    root = pathlib.Path(root) if root is not None else _ROOT
    sidecar = run_sidecar(root)
    _prove(sidecar.exists(), f"{sidecar} is missing: there is no E5 run to cross-check")
    blob = _load(sidecar)
    _prove(blob["status"] == "SCORED", f"the run is {blob['status']}, not SCORED: nothing to check")
    out = cpu_sidecar(root)
    _prove(not out.exists(), f"{out} exists: the CPU cross-check is write-once")
    plan = scoring_plan(slots=blob["slots"], max_size=blob["max_size"])
    state = {"point": RUN_ID, "stage": "crosscheck", "shape": None, "draw_index": None}
    started, gate, ranks = _now(), {}, {}
    for reading in blob["readings"]:
        with reading_model(reading, device) as (model, tok):
            nll_by_slot = {}
            for slot in plan:
                references = phase18_extraction.reference_set_for(slot)
                nlls = score_values(model, tok, device, slot, references, state)
                nll_by_slot[slot] = dict(zip(references, nlls))
            gate[reading] = {s: r["rank"] for s, r in gate_reading(reading, nll_by_slot).items()}
            ranks[reading] = {}
            for slot, row in plan.items():
                nlls = score_values(
                    model, tok, device, slot, [row["taught"], *row["minted"]], state
                )
                curve = curve_for(row["taught"], nlls[0], row["minted"], nlls[1:], row["sizes"])
                ranks[reading][slot] = {size: cell["rank"] for size, cell in curve.items()}
    _write_once(
        out,
        {
            "device": device,
            "torch_version": torch.__version__,
            "started_utc": started,
            "finished_utc": _now(),
            "gate": gate,
            "ranks": ranks,
        },
    )
    print(f"CROSSCHECK DONE {out}", flush=True)
    return out


def _hours(started, finished):
    delta = datetime.datetime.fromisoformat(finished) - datetime.datetime.fromisoformat(started)
    return delta.total_seconds() / 3600


def _events(curves, slots, sizes, a2):
    """D-12 / D-29 / D-30 / WR-01 over the six PREFIXES only (D-16), per slot and nested size."""
    events = {}
    for slot in slots:
        counts, n = a2[slot]["counts"], a2[slot]["n_questions"]
        collapse = prereg.first_collapse(counts)
        damage = prereg.first_damage(counts, n)
        events[slot] = {}
        for size in sizes[slot]:
            ranks = {k: curves[f"k{k}"][slot]["curve"][str(size)]["rank"] for k in prereg.PREFIXES}
            rank_0 = ranks[0]
            definitions = {
                "moved": (
                    {k: prereg.moved(r, rank_0) for k, r in ranks.items()},
                    prereg.moved_reachable(rank_0, size),
                ),
                "left_top_eighth": (
                    {k: prereg.left_top_eighth(r, size) for k, r in ranks.items()},
                    True,
                ),
            }
            events[slot][str(size)] = {}
            for name, (flags, reachable) in definitions.items():
                first = prereg.first_event(flags)
                events[slot][str(size)][name] = {
                    "flags": {str(k): flag for k, flag in flags.items()},
                    "first": first,
                    "rank_0": rank_0,
                    "reachable": reachable,
                    "vs_collapse": prereg.relation(first, collapse, reachable=reachable),
                    "vs_damage": prereg.relation(first, damage, reachable=reachable),
                }
    return events


def _cpu_block(cpu, curves, gate_rows, slots, sizes):
    cells = [[reading, slot, size] for reading in curves for slot in slots for size in sizes[slot]]
    differing = [
        [r, s, size]
        for r, s, size in cells
        if cpu["ranks"][r][s][str(size)] != curves[r][s]["curve"][str(size)]["rank"]
    ]
    gate_cells = [[r, s] for r, rows in gate_rows.items() for s in rows]
    gate_differing = [[r, s] for r, s in gate_cells if cpu["gate"][r][s] != gate_rows[r][s]["rank"]]
    return {
        "criterion": False,
        "note": "D-19: descriptive only, never a criterion",
        "device": cpu["device"],
        "torch_version": cpu["torch_version"],
        "cells": len(cells),
        "differing": len(differing),
        "differing_cells": differing,
        "gate_cells": len(gate_cells),
        "gate_differing": len(gate_differing),
        "gate_differing_cells": gate_differing,
    }


def build_record(root):
    """The E5 record, only from the sidecars and through the frozen phase38_prereg definitions."""
    root = pathlib.Path(root)
    blob = _load(run_sidecar(root))
    _prove(
        _sha256(gate_sidecar(root)) == blob["gate_sha256"],
        f"{gate_sidecar(root)} is not the bytes the run wrote (run sidecar SHA-256)",
    )
    gate = _load(gate_sidecar(root))
    record = {
        "front": FRONT,
        "run_id": RUN_ID,
        "status": blob["status"],
        "approval": prereg.approval_block(),
        "minting_record": {
            "path": prereg.MINTING_RECORD,
            "sha256": _sha256(_REPO / prereg.MINTING_RECORD),
        },
        "set_sizes": blob["sizes"],
        "reconstruction": blob["reconstruction"],
        "gate": gate,
        "cost": {
            "run_hours": _hours(blob["started_utc"], blob["finished_utc"]),
            "e5_projection_hours": prereg.E5_PROJECTION_HOURS,
            "e5_stop_hours": prereg.E5_STOP_HOURS,
        },
    }
    if _is_real(root):
        identity = rehearsal_identity_path()
        _prove(identity.exists(), f"{identity} is missing: the D-34 disclosure needs it")
        record["rehearsal_disclosure"] = rehearsal_disclosure(
            _load(identity),
            launch_git_sha=blob["git_sha_at_launch"],
            launch_module_sha256=blob["module_sha256_at_launch"],
        )
    else:
        record["rehearsal_disclosure"] = {"this_is_the_rehearsal": True}
    sidecars = {"run": _sha256(run_sidecar(root)), "gate": blob["gate_sha256"]}
    if blob["status"] == "SCORED":
        cpu_path = cpu_sidecar(root)
        _prove(cpu_path.exists(), f"{cpu_path} is missing: run crosscheck before emit (D-19)")
        minting = _json(prereg.MINTING_RECORD)["slots"]
        slots = blob["slots"]
        sizes = {slot: list(prereg.nested_sizes(blob["sizes"][slot])) for slot in slots}
        curves, sensitivity = {}, {}
        for reading in blob["readings"]:
            path = nll_sidecar(root, reading)
            _prove(
                _sha256(path) == blob["nll_sha256"].get(reading),
                f"{path} is not the bytes the run wrote (run sidecar SHA-256)",
            )
            curves[reading] = {}
            for slot, row in _load(path)["slots"].items():
                _prove(
                    row["minted"] == minting[slot]["cleared"][: blob["sizes"][slot] - 1],
                    f"{path} {slot}: the scored values are not the minting record's prefix",
                )
                args = (row["taught"], row["taught_nll"], row["minted"], row["minted_nll"])
                curves[reading][slot] = {
                    "taught_nll": row["taught_nll"],
                    "minted_nll": row["minted_nll"],
                    "curve": curve_for(*args, sizes[slot]),
                }
                if "neighbour_d1" in minting[slot]:
                    block = sensitivity.setdefault(
                        slot,
                        {
                            "descriptive": True,
                            "note": "D-27: ranks without the distance-1 neighbours of a taught "
                            "value; never enters any definition",
                            "curves": {},
                        },
                    )
                    block["curves"][reading] = curve_for(
                        *args, sizes[slot], exclude=minting[slot]["neighbour_d1"]
                    )
        a2 = prereg.a2_counts()
        missing = [f"k{k}" for k in prereg.PREFIXES if f"k{k}" not in curves]
        cpu = _load(cpu_path)
        sidecars.update(cpu=_sha256(cpu_path), nll=blob["nll_sha256"])
        record.update(
            readings=curves,
            descriptive_readings=["M2", "adapter_off"],
            descriptive_note="D-11 / D-16: M2 and adapter-off are descriptive references; they "
            "enter neither moved, left the top eighth, collapsed nor damaged",
            committed_reference_sets=gate["rows"],
            sensitivity_numeric=sensitivity,
            events=None if missing else _events(curves, slots, sizes, a2),
            a2={
                slot: {
                    "n_questions": a2[slot]["n_questions"],
                    "counts": {str(k): c for k, c in a2[slot]["counts"].items()},
                    "first_collapse": prereg.first_collapse(a2[slot]["counts"]),
                    "first_damage": prereg.first_damage(
                        a2[slot]["counts"], a2[slot]["n_questions"]
                    ),
                    "margin": prereg.MARGIN,
                }
                for slot in slots
            },
            drop_formula_audit=prereg.drop_formula_audit(a2),
            cpu_crosscheck=_cpu_block(cpu, curves, gate["rows"], slots, sizes),
        )
        if missing:
            record["events_reason"] = (
                f"a rehearsal subset without the readings {missing}: the events are defined over "
                f"all six prefixes {list(prereg.PREFIXES)}"
            )
    launch, now = blob["module_sha256_at_launch"], module_sha256()
    record["provenance"] = {
        "run": {key: blob[key] for key in RUN_PROVENANCE_KEYS},
        "module_sha256_at_launch": launch,
        "module_sha256": now,
        "modules_changed_since_launch": sorted(
            rel for rel in MODULES if launch.get(rel) != now[rel]
        ),
        "sidecar_sha256": sidecars,
        "head_at_write": git_sha(),
        "written_utc": _now(),
    }
    return record


def emit(*, root=None):
    """Write results/phase38_rank.json ONCE from the sidecars (D-22, SC4)."""
    root = pathlib.Path(root) if root is not None else _ROOT
    out = root / prereg.RANK_RECORD
    _prove(
        not out.exists(),
        f"{out} exists — REFUSING to overwrite it. The E5 record is write-once; corrections are "
        "dated continuations",
    )
    sidecar = run_sidecar(root)
    _prove(sidecar.exists(), f"{sidecar} is missing: there is no E5 run to emit")
    blob = _load(sidecar)
    _prove(
        not _is_real(root)
        or (
            blob["readings"] == list(prereg.READINGS)
            and blob["slots"] == list(prereg.SLOTS)
            and blob["max_size"] is None
        ),
        "the real root emits the full READINGS x SLOTS x E5_SET_SIZES shape only",
    )
    pathspec = LAUNCH_PATHSPEC
    if out.resolve().is_relative_to(_REPO.resolve()):
        pathspec = (*LAUNCH_PATHSPEC, f":(exclude){prereg.RANK_RECORD}")
    refuse_if_dirty(
        who="phase38_rank",
        detail=(
            "the E5 record publishes git_sha and hashes its modules from the working tree; a "
            "record written from a dirty tree names a commit it cannot be regenerated from"
        ),
        pathspec=pathspec,
        cwd=_REPO,
    )
    record = build_record(root)
    phase25_run.atomic_write_json(out, record)
    print(f"EMITTED {record['status']} {out}", flush=True)
    return record
