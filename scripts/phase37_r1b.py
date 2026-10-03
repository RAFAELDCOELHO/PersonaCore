"""Phase 37 R1b (REPRO-03) — the MPS replica of the Phase 19 erased arm at k = 78.

    .venv/bin/python scripts/phase37_r1b.py preflight   # every refusal, writes nothing
    .venv/bin/python scripts/phase37_r1b.py run         # THE attempt: sweep -> D-07 -> arm -> emit
    .venv/bin/python scripts/phase37_r1b.py emit        # CPU: rebuild the record from the sidecar

WHAT IS RE-MEASURED AND WHAT IS INHERITED (D-05). `run` redoes the selection sweep through the
defect-E routing (`phase37_routes.select_target_prefix`, |R| = 8), so k is MEASURED, then runs the
pin's erased arm at K = 48 on the re-measured prefix. The record states both lists by assertion,
read from `phase37_prereg.ENTRIES["r1b_scope"]`: the committed prefix is only the D-07 comparator,
and the adapter's SHA-256 must equal the committed curve's `adapter_in_sha256`.

D-07. k == 78 and the SAME set of addresses as the committed prefix -> the arm runs on the
re-measured list (same set, bit-identical weights whatever the order; positions moved is
description). k != 78 or another set -> the arm does NOT run and the record reads NOT_REPLICATED
with k and the set difference as its verdict fields. The sweep is recorded in BOTH branches (D-14).

D-03. REPLICATED / NOT_REPLICATED comes only from `phase37_prereg.replicated` over
`phase37_routes.rederive` of the replica arm — the same rederive R1a runs. Draw bit-identity
against results/phase19_arm_erased.json and the per-slot non-target context (D-04 / D-12) sit
beside it, labelled `criterion: False`.

ONE ATTEMPT (D-11, D-15, D-16). The attempt starts at the ledger start line. Every cheap refusal
(existing records or sidecar, any ledger line for RUN_ID, a dirty tree, `require_launch("R1b")`, a
device other than MPS, a missing input file, an adapter that is not the curve's) runs BEFORE that
line and is not an attempt. Once the start line is written the attempt is THE attempt: a crash
before the sidecar leaves an open start that `phase36_ledger.reconcile` turns into a lost line; a
crash after the sidecar is closed by an end line and `emit`, never reconciled.

It is launched only by Rafael, after his "approved" and a passing `require_launch("R1b")`, through
artifacts/com.personacore.phase37.r1b.plist. The Phase 19 retrain and replicate arms are out of
scope. It never calls `phase19_run.report()`, never writes a Phase 19 path and never calls the
pin's sweep except through the defect-E wrapper.
"""

import datetime
import fnmatch
import hashlib
import json
import os
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import phase19_erasure as pin  # noqa: E402
import phase19_run as p19run  # noqa: E402  — TARGET_CURVE_PATH only
import phase25_run  # noqa: E402  — beat, start_heartbeat, atomic_write_json
import phase36_ledger  # noqa: E402
import phase37_prereg as prereg  # noqa: E402
import phase37_routes as routes  # noqa: E402

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402

_ROOT = pathlib.Path(__file__).resolve().parent.parent
FRONT = "R1b"
RUN_ID = phase36_ledger.run_id(37, FRONT, "replica")
LAUNCH_PATHSPEC = ("scripts", "src", "results")
MODULES = (
    "scripts/phase19_erasure.py",
    "scripts/erasure_gate.py",
    "scripts/phase19_run.py",
    "scripts/phase35_prereg.py",
    "scripts/phase36_ledger.py",
    "scripts/phase37_prereg.py",
    "scripts/phase37_routes.py",
    "scripts/phase37_r1b.py",
)


def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[phase37_r1b] {message}")


def _sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def run_sidecar(root):
    """The gitignored run sidecar: written before the ledger end line, read by `emit`."""
    return pathlib.Path(root) / "data" / "phase37_r1b_run.json"


def adapter_sha256():
    import phase14_recall

    return _sha256(phase14_recall.ADAPTER_PATH)


def run_inputs():
    """WR-03: every input file the run reads, from the constants its readers take them from.

    `refuse_if_dirty` cannot see the gitignored ones (checkpoints/, data/), so without this a
    missing file crashes AFTER the ledger start line and burns the one attempt (D-11, D-16).
    """
    import phase14_recall as recall
    import teach_persona as tp

    return (
        recall.CONVBASE_SLIM,  # load_adapted_model: the sweep's and the arm's base
        recall.ADAPTER_PATH,  # load_adapted_model, adapter_sha256
        recall.TOKENIZER_PATH,  # load_adapted_model
        tp.DIALOG_VAL_BIN,  # pin.dialogue_ppl_pair: the sweep's curve rows and the arm
        tp.DIALOG_VAL_MASK,  # same
        pin.RETENTION_BIN,  # run_erasure_arm's retention_perplexity
        pin.PHASE18_CORPUS_PATH,  # run_erasure_arm's corpus_path default
        pin.PHASE18_ARM_RECORD_PATH,  # run_erasure_arm: pre-erasure per_fact and attack family
    )


def _device():
    from personacore.preflight import preflight_device

    return preflight_device(strict=True)["device"]


def _curve():
    import phase18_extraction

    curve = json.loads(p19run.TARGET_CURVE_PATH.read_text(encoding="utf-8"))
    _prove(curve["slot"] == pin.TARGET_SLOT, f"curve slot {curve['slot']!r} != {pin.TARGET_SLOT!r}")
    _prove(curve["stopped"] is True, "the committed curve did not stop")
    _prove(
        len(curve["ordered_prefix"]) == curve["k"],
        f"ordered_prefix holds {len(curve['ordered_prefix'])} addresses, not k = {curve['k']}",
    )
    references = phase18_extraction.reference_set_for(pin.TARGET_SLOT)
    _prove(
        curve["reference_set_size"] == len(references),
        f"the curve was read on |R| = {curve['reference_set_size']}, not the "
        f"reference_set_for |R| = {len(references)} (defect E's path)",
    )
    return curve


def preflight(*, root=None, ledger_path=None):
    """Every refusal before the ledger start line (D-16). Writes nothing."""
    root = pathlib.Path(root) if root is not None else _ROOT
    for path in (root / prereg.R1B_RECORD, root / prereg.R1B_ARM_RECORD, run_sidecar(root)):
        _prove(not path.exists(), f"{path} exists: the one R1b attempt has already run (D-11)")
    _prove(
        not any(line["run_id"] == RUN_ID for line in phase36_ledger.read_ledger(ledger_path)),
        f"the ledger already holds a line for {RUN_ID}: the one R1b attempt has started (D-11). "
        'D-11 allows a relaunch only after Rafael\'s "approved", a ledger reconcile and a '
        "root-cause note. Separately, as an implementation fact and not part of D-11, this driver "
        f"refuses to write any second line for {RUN_ID}",
    )
    refuse_if_dirty(
        who="phase37_r1b",
        detail=(
            "the R1b record publishes git_sha and hashes its modules from the working tree; an "
            "attempt launched from a dirty tree names a commit it cannot be regenerated from"
        ),
        pathspec=LAUNCH_PATHSPEC,
        cwd=_ROOT,
    )
    gate = phase36_ledger.require_launch(FRONT, ledger_path=ledger_path)
    device = _device()
    _prove(device == "mps", f"R1b is the MPS replica; preflight resolved {device!r}")
    for path in run_inputs():
        _prove(
            pathlib.Path(path).exists(),
            f"{path} is missing: the run reads it, so this refuses before the ledger start line "
            "(D-16) instead of crashing after it",
        )
    curve = _curve()
    _prove(
        adapter_sha256() == curve["adapter_in_sha256"],
        "the production adapter is not the one the committed curve was swept on",
    )
    print(
        f"PREFLIGHT OK {git_sha()} device={device} cost={prereg.R1B_COST_HOURS} h "
        f"cap={prereg.R1B_COST_CAP_HOURS} h",
        flush=True,
    )
    return {"device": device, "curve": curve, "gate": gate}


def run(*, root=None, ledger_path=None, heartbeat_path=None):
    """THE attempt: preflight, ledger start, sweep, D-07, arm, sidecar, ledger end, emit."""
    root = pathlib.Path(root) if root is not None else _ROOT
    pre = preflight(root=root, ledger_path=ledger_path)
    device, curve = pre["device"], pre["curve"]
    heartbeat_path = heartbeat_path or phase36_ledger.HEARTBEAT_PATH
    phase36_ledger.append("start", run_id=RUN_ID, phase=37, front=FRONT, ledger_path=ledger_path)
    state = {"point": RUN_ID, "stage": "sweep", "shape": None, "draw_index": None}
    # B1: the thread's first beat comes only after its first wait: beat once now.
    phase25_run.beat(heartbeat_path, **state)
    stop, thread = phase25_run.start_heartbeat(heartbeat_path, state)
    started_utc = _now()
    try:
        import gc

        import phase14_factset as factset
        import phase14_recall as recall
        import phase18_extraction
        import torch

        model, _cfg, tok, forbid, artifact = recall.load_adapted_model(device, recall.ADAPTER_PATH)
        target = {f.slot: f for f in factset.LOCKED_FACTS}[pin.TARGET_SLOT]
        t0 = time.monotonic()
        chosen = routes.select_target_prefix(
            model,
            tok,
            device,
            artifact,
            fact=target,
            dialogue_ppl=lambda: pin.dialogue_ppl_pair(model, device, forbid),
        )
        remeasured = [tuple(a) for a in chosen["ordered"][: chosen["k"]]]
        sweep = {
            "k": chosen["k"],
            "stopped": chosen["stopped"],
            "cap": chosen["cap"],
            "ordered_prefix": [list(a) for a in remeasured],
            "intact_nll": chosen["intact_nll"],
            "curve": chosen["curve"],
            "wall_clock_min": (time.monotonic() - t0) / 60,
            "reference_set_size": len(phase18_extraction.reference_set_for(target.slot)),
        }
        decision = prereg.prefix_decision(
            chosen["k"], remeasured, [tuple(a) for a in curve["ordered_prefix"]]
        )
        model = artifact = None  # release the sweep model: the arm loads its own
        gc.collect()
        if torch.backends.mps.is_available():  # never reached on a CPU-only host (ubuntu CI)
            torch.mps.empty_cache()
        if decision["run_arm"]:
            state.update(stage="arm")
            pin.run_erasure_arm(
                "erased", device, components=remeasured, record_path=root / prereg.R1B_ARM_RECORD
            )
        _prove(
            adapter_sha256() == curve["adapter_in_sha256"],
            "the production adapter changed during the run — it must stay intact",
        )
        # Nothing between the arm and this write raises except a real failure; from here on the
        # attempt's output survives any post-processing error: `emit` rebuilds the record on CPU.
        run_sidecar(root).parent.mkdir(parents=True, exist_ok=True)
        phase25_run.atomic_write_json(
            run_sidecar(root),
            {
                "run_id": RUN_ID,
                "git_sha": git_sha(),
                "device": device,
                "torch_version": torch.__version__,
                "started_utc": started_utc,
                "finished_utc": _now(),
                "sweep": sweep,
                "decision": decision,
                "arm_ran": decision["run_arm"],
            },
        )
        state.update(stage="done")
    finally:
        stop.set()
        thread.join()
    phase36_ledger.append(
        "end",
        run_id=RUN_ID,
        phase=37,
        front=FRONT,
        record=prereg.R1B_RECORD,
        ledger_path=ledger_path,
    )
    return emit(root=root)


def build_record(blob, *, root):
    """The R1b record from the run sidecar ``blob`` (and the replica arm record when it ran)."""
    root = pathlib.Path(root)
    erased_path = pin.arm_record_path("erased")
    committed = json.loads(erased_path.read_text(encoding="utf-8"))
    scope = prereg.ENTRIES["r1b_scope"]["value"]
    filled = prereg.R1B_TOLERANCE_AND_REPLICATED
    record = {
        "verdict": None,
        "decision": blob["decision"],
        "sweep": blob["sweep"],  # D-14: both branches
        "tolerance": dict(filled["tolerance"]),
        "replicated_definition": dict(filled["replicated_definition"]),
        "re_measured": list(scope["re_measured"]),
        "inherited": list(scope["inherited"]),
        "committed_comparators": {
            pathlib.Path(p).resolve().relative_to(_ROOT).as_posix(): _sha256(p)
            for p in (p19run.TARGET_CURVE_PATH, erased_path)
        },
        "arm_record": None,
    }
    if blob["arm_ran"]:
        arm_path = root / prereg.R1B_ARM_RECORD
        replica = json.loads(arm_path.read_text(encoding="utf-8"))
        rederived = routes.rederive(replica)
        comparison = prereg.replicated(rederived)
        record.update(
            verdict=comparison["verdict"],
            comparison=comparison,
            replica_verdict=rederived["verdict"],
            replica_reasons=rederived["reasons"],
            draw_identity=prereg.draw_identity(replica["draws"], committed["draws"]),
            nontarget_context=prereg.nontarget_context(
                rederived["nontarget_deltas_by_slot"],
                routes.rederive(committed)["nontarget_deltas_by_slot"],
            ),
            arm_record=prereg.R1B_ARM_RECORD,
            arm_record_sha256=_sha256(arm_path),
        )
    else:
        record["verdict"] = prereg.ENTRIES["not_replicated_rule"]["value"]
    record["provenance"] = {
        "run": {
            key: blob[key]
            for key in ("git_sha", "device", "torch_version", "started_utc", "finished_utc")
        },
        "module_sha256": {rel: _sha256(_ROOT / rel) for rel in MODULES},
        "head_at_write": git_sha(),
        "written_utc": _now(),
    }
    return record


def emit(*, root=None):
    """Write results/phase37_r1b.json ONCE from the sidecar. Re-runnable on CPU after a crash."""
    root = pathlib.Path(root) if root is not None else _ROOT
    out = root / prereg.R1B_RECORD
    rel = out.relative_to(root).as_posix()
    _prove(fnmatch.fnmatch(rel, prereg.RECORD_GLOB), f"{rel} does not match {prereg.RECORD_GLOB}")
    _prove(
        not out.exists(),
        f"{out} exists — REFUSING to overwrite it. The R1b record is write-once; corrections are "
        "dated continuations",
    )
    sidecar = run_sidecar(root)
    _prove(sidecar.exists(), f"{sidecar} is missing: there is no R1b run to emit")
    refuse_if_dirty(
        who="phase37_r1b",
        detail=(
            "the R1b record publishes git_sha and hashes its modules from the working tree; a "
            "record written from a dirty tree names a commit it cannot be regenerated from"
        ),
        pathspec=(
            *LAUNCH_PATHSPEC,
            f":(exclude){prereg.R1B_ARM_RECORD}",
            f":(exclude){prereg.R1B_RECORD}",
        ),
        cwd=_ROOT,
    )
    record = build_record(json.loads(sidecar.read_text(encoding="utf-8")), root=root)
    phase25_run.atomic_write_json(out, record)
    print(f"R1b {record['verdict']} {out}", flush=True)
    return record


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    commands = {"preflight": preflight, "run": run, "emit": emit}
    if len(argv) != 1 or argv[0] not in commands:
        raise SystemExit(__doc__)
    # WR-05: git_sha() (this driver's and the pin arm record's) reads the process cwd; run at the
    # repo root whatever the launch directory, so no record names "unknown" or another checkout.
    os.chdir(_ROOT)
    return commands[argv[0]]()


if __name__ == "__main__":
    main(sys.argv[1:])
