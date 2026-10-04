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
