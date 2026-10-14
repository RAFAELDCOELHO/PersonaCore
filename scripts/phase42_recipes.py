"""Phase 42 E3 (RECIPE-01..RECIPE-04) — DP-SGD recipe search at large epsilon.

    .venv/bin/python scripts/phase42_recipes.py preflight   # the launch checks, writes nothing
    .venv/bin/python scripts/phase42_recipes.py run         # the pending controls, then the points
    .venv/bin/python scripts/phase42_recipes.py emit        # CPU: the E3 record
    .venv/bin/python scripts/phase42_recipes.py report      # the markdown from the E3 record

The grid, the units, the record paths, the warmup, the clip and every reading come from
``scripts/phase42_prereg.py`` (frozen, read through ``_prereg()``, never restated here). Training
reaches the trainer only through ``phase25_points.train_stage``, with teach_persona's ``LR`` /
``WARMUP_STEPS`` / ``MAX_STEPS`` rebound for that one call and restored after it (D-05, the
``phase36_probe.stage_e3`` precedent); the constants are never edited, and every take is proved
from the training sidecar's ``train_config`` and ``live_mechanism``.

Torch-free at import: every torch-importing module and the pre-registration are imported inside
the functions that need them.
"""

import datetime
import gc
import hashlib
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import phase25_points  # noqa: E402  (torch-free at import; the one training stage)
import phase25_record  # noqa: E402  (torch-free; point_key)
import phase25_run  # noqa: E402  — atomic_write_json, beat, start_heartbeat (torch-free)
import phase35_prereg  # noqa: E402  (torch-free at import; E3_N, DELTA, p22_onset_sigma)
import phase36_ledger  # noqa: E402  (torch-free; the per-unit attempt)

# FIXED: the cwd of every git call and the base of the module digests.
_REPO = pathlib.Path(__file__).resolve().parent.parent
# The default OUTPUT root (results/, data/) and the identity that selects the real-root branches.
_ROOT = _REPO
FRONT = "E3"
LAUNCH_PATHSPEC = ("scripts", "src", "results", "artifacts")
PREREG_FILE = "scripts/phase42_prereg.py"
# Not in DISCLOSED_MODULES: it does not exist until plan 42-09 (stage() reads it).
THRESHOLD_FILE = "scripts/phase42_threshold_prereg.py"
DRIVER_FILE = "scripts/phase42_recipes.py"
DISCLOSED_MODULES = (DRIVER_FILE, PREREG_FILE)
MODULES = DISCLOSED_MODULES + (
    "scripts/phase35_prereg.py",
    "scripts/phase25_points.py",
    "scripts/teach_persona.py",
    "scripts/phase25_condition_c.py",
    "scripts/phase25_epsilon.py",
    "scripts/phase25_recall.py",
    "scripts/phase14_recall.py",
    "scripts/phase29_prereg.py",
    "scripts/phase36_ledger.py",
    "scripts/phase36_caps.py",
    "scripts/phase25_run.py",
    "src/personacore/privacy/dpsgd.py",
    "src/personacore/privacy/accountant.py",
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
# Gitignored (data/); recorded by the CPU rehearsal, read by the real-root preflight.
REHEARSAL_IDENTITY = "data/phase42_rehearsal.json"
STAGE_1_DONE = (
    "STAGE 1 DONE: commit the control records, then scripts/phase42_threshold_prereg.py (D-19), "
    "before stage 2"
)


def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[phase42_recipes] {message}")


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
    """phase42_prereg, imported lazily (torch at import through teach_persona)."""
    import phase42_prereg

    return phase42_prereg


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


# =================================================================================================
# The cell plan and the D-05 training seam (D-05, D-06, D-07; crash_rule, 42-RESEARCH Pitfall 1)
# =================================================================================================


def cell_plan(unit, *, rehearsal):
    """The v4.0 point plan of the unit's sigma (``phase25_points.point_plan``), re-keyed to the
    unit's training prefix, its pinned step count set to the recipe's T. point_epsilon /
    accounting are None: point_plan computes them at T = STEP_BUDGET, never read here (D-14)."""
    prereg = _prereg()
    recipe, sigma = prereg.unit_cell(unit)
    base = phase25_points.point_plan(phase25_record.point_key(f"dp_n{phase35_prereg.E3_N}", sigma))
    _prove(base["dp_sigma"] == sigma, f"{unit}: point_plan sigma {base['dp_sigma']!r} != {sigma}")
    _prove(
        base["dp_clip_norm"] == prereg.clip_norm_for(sigma),
        f"{unit}: point_plan clip {base['dp_clip_norm']!r} is not the pre-registered "
        f"{prereg.clip_norm_for(sigma)!r} (D-06 / D-07)",
    )
    _prove(base["seed"] == prereg.SEED, f"{unit}: seed {base['seed']!r} is not {prereg.SEED}")
    prefix = prereg.train_prefix(unit, rehearsal=rehearsal)
    return dict(
        base,
        point_key=prefix,
        prefix=prefix,
        pinned_mechanism=dict(base["pinned_mechanism"], composed_steps=recipe["steps"]),
        point_epsilon=None,
        accounting=None,
    )


def _schedule_of(recipe):
    """(lr, warmup_steps, max_steps) of a recipe: the three values the D-05 seam rebinds."""
    return recipe["lr"], _prereg().warmup_for(recipe["steps"]), recipe["steps"]


def _resume_guard(plan, recipe):
    """Pitfall 1: a latest.pt without a finished sidecar is resumed by train_stage; refuse it unless
    its train_config ran this cell's lr / warmup_steps / max_steps (no resume under another
    schedule). A finished sidecar is reused by train_stage and proved by the take proof."""
    import teach_persona as tp  # torch at import: lazy

    checkpoint = tp.arm_outputs(plan["arm"], prefix=plan["prefix"])["checkpoint"]
    if not checkpoint.exists() or phase25_points.training_sidecar(plan["point_key"]).exists():
        return
    config = tp.torch.load(checkpoint, weights_only=False)["train_config"]
    found = (config["lr"], config["warmup_steps"], config["max_steps"])
    _prove(
        found == _schedule_of(recipe),
        f"{checkpoint} was trained at (lr, warmup_steps, max_steps) = {found}, not this cell's "
        f"{_schedule_of(recipe)}: a resume under another schedule is refused (42-RESEARCH "
        "Pitfall 1)",
    )


def train_cell(unit, *, rehearsal):
    """D-05: ONE phase25_points.train_stage call with teach_persona's LR / WARMUP_STEPS / MAX_STEPS
    rebound to the recipe's (restored in finally, also on a raise), then the take proved from the
    sidecar blob. Returns ``(plan, blob)``."""
    import teach_persona as tp  # torch at import: lazy

    prereg = _prereg()
    recipe, sigma = prereg.unit_cell(unit)
    plan = cell_plan(unit, rehearsal=rehearsal)
    _resume_guard(plan, recipe)
    saved = (tp.LR, tp.WARMUP_STEPS, tp.MAX_STEPS)
    tp.LR, tp.WARMUP_STEPS, tp.MAX_STEPS = _schedule_of(recipe)
    try:
        blob = phase25_points.train_stage(plan)
    finally:
        tp.LR, tp.WARMUP_STEPS, tp.MAX_STEPS = saved
    expected = dict(prereg.expected_train_config(recipe))
    _prove(
        dict(blob["train_config"]) == expected,
        f"{unit}: the sidecar's train_config {blob['train_config']} is not the pre-registered "
        f"{expected} (D-05 / D-07)",
    )
    live = blob["live_mechanism"]
    _prove(
        live["composed_steps"] == recipe["steps"],
        f"{unit}: the seam composed {live['composed_steps']} steps, not T = {recipe['steps']}",
    )
    _prove(
        live["clip_norm"] == prereg.clip_norm_for(sigma),
        f"{unit}: the seam clipped at {live['clip_norm']!r}, not {prereg.clip_norm_for(sigma)!r}",
    )
    return plan, blob
