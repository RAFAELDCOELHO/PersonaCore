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
