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
import json
import pathlib
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import phase25_points  # noqa: E402  (torch-free at import; the one training stage)
import phase25_record  # noqa: E402  (torch-free; point_key)
import phase25_run  # noqa: E402  — atomic_write_json, beat, start_heartbeat (torch-free)
import phase35_prereg  # noqa: E402  (torch-free at import; E3_N, DELTA, p22_onset_sigma)
import phase36_caps  # noqa: E402  (torch-free at import; the launch caps)
import phase36_ledger  # noqa: E402  (torch-free; the per-unit attempt)

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402

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


# =================================================================================================
# Scoring, the descriptive retention reading and the write-once unit record (RECIPE-02, D-13, D-16)
# =================================================================================================


def score(plan, adapter, device):
    """The v4.0 instrument and record shape (D-16 comparability): teach_persona.score_arm on the
    locked facts, each block in phase25_recall._tier's numerator / denominator shape."""
    import phase14_factset as fs  # fact material: lazy
    import phase25_recall
    import teach_persona as tp  # torch at import: lazy

    started = time.monotonic()
    out = tp.score_arm(plan["arm"], fs.LOCKED_FACTS, adapter, device)
    seconds = time.monotonic() - started
    return {
        "taught_recall": phase25_recall._tier(out["on_taught"]),
        "heldout_recall": phase25_recall._tier(out["on_heldout"]),
        "taught_recall_off": phase25_recall._tier(out["off_taught"]),
        "heldout_recall_off": phase25_recall._tier(out["off_heldout"]),
        "per_family_gain": out["per_family_gain"],
        "scoring_seconds": seconds,
    }


def retention(adapter, device):
    """D-13, descriptive: condition (c) on ONE loaded adapted model, through
    phase25_condition_c.measure_condition_c (the only retention path this driver reaches)."""
    import phase14_recall  # torch at import: lazy
    import phase25_condition_c

    started = time.monotonic()
    model, _cfg, tok, forbid, _artifact = phase14_recall.load_adapted_model(device, adapter)
    reading = dict(phase25_condition_c.measure_condition_c(model, tok, device, forbid=forbid))
    del model
    _release()
    reading["seconds"] = time.monotonic() - started
    return reading


def _run_provenance(pf, started_utc):
    import torch

    end_sha = git_sha()
    return {
        "git_sha_at_launch": pf["git_sha"],
        "git_sha_at_end": end_sha,
        "head_moved_during_run": end_sha != pf["git_sha"],
        "device": pf["device"],
        "torch_version": torch.__version__,
        "started_utc": started_utc,
        "finished_utc": _now(),
    }


def write_unit(unit, *, pf, started_utc, state):
    """One unit inside its ledger attempt: write-once checked FIRST, the D-05 seam, the adapter
    digest, the v4.0 scoring, the descriptive retention, then the record (epsilon at the unit's
    own T, None at a control; the refusal leg declared omitted, never measured). Returns the
    record's repo-relative path (the end line names it)."""
    prereg = _prereg()
    root = pathlib.Path(pf["root"])
    rel = prereg.unit_record(unit)
    out = root / rel
    _prove(not out.exists(), f"{out} exists: write-once")
    recipe, sigma = prereg.unit_cell(unit)
    state.update(stage="train")
    plan, blob = train_cell(unit, rehearsal=not pf["real"])
    adapter = phase25_points._ROOT / blob["adapter"]
    _prove(
        _sha256(adapter) == blob["adapter_sha256"],
        f"{adapter} is not the adapter the sidecar records ({blob['adapter_sha256']}): refused "
        "before scoring",
    )
    state.update(stage="score")
    scores = score(plan, adapter, pf["device"])
    state.update(stage="retention")
    capability = retention(adapter, pf["device"])
    live = blob["live_mechanism"]
    lost = [
        line
        for line in phase36_ledger.read_ledger(pf["ledger_path"])
        if line["event"] == "lost" and line["run_id"] == prereg.run_id(unit)
    ]
    record = {
        "unit": unit,
        "recipe": dict(recipe),
        "seed": prereg.SEED,
        "sigma": sigma,
        "n_facts": blob["n_facts"],
        "clip_norm": live["clip_norm"],
        **scores,
        "epsilon": prereg.point_epsilon(sigma, recipe["steps"]),
        "delta": phase35_prereg.DELTA,
        "selection_accounted": prereg.SELECTION_ACCOUNTED,
        "accounting": {
            "q": live["q"],
            "composed_steps": live["composed_steps"],
            "composed_lot_sizes": live["composed_lot_sizes"],
        },
        "clip_bind_count": blob["clip_bind_count"],
        "dialogue_gap": blob["ppl_adapter_on"] - blob["ppl_adapter_off"],
        "condition_c": capability,
        "descriptive": ("clip_bind_count", "dialogue_gap", "condition_c"),
        "refusal": prereg.ENTRIES["refusal_omitted"]["derivation"],
        "training": dict(blob),
        "lost_attempts": lost,
        "provenance": {"run": _run_provenance(pf, started_utc)},
        "module_sha256_at_launch": pf["module_sha256"],
    }
    if not pf["real"]:
        record["rehearsal_disclosure"] = {"this_is_the_rehearsal": True}
    _write_once(out, record)
    state.update(stage="done")
    return rel


# =================================================================================================
# The rehearsal identity (D-21; 38-REVIEW DR-02 / DR-03)
# =================================================================================================

_IDENTITY_KEYS = frozenset({"git_sha", "module_sha256", "units", "started_utc", "cpu_seconds"})


def _load(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def _disclosed_digests():
    return {rel: _sha256(_REPO / rel) for rel in DISCLOSED_MODULES}


def _well_formed(identity):
    return (
        isinstance(identity, dict)
        and set(identity) == _IDENTITY_KEYS
        and isinstance(identity["module_sha256"], dict)
        and set(identity["module_sha256"]) == set(DISCLOSED_MODULES)
        and isinstance(identity["units"], list)
    )


def _kept_identity(path):
    """The identity already at ``path`` (None when absent), refused when malformed or recorded at
    other DISCLOSED_MODULES digests: a changed driver or prereg needs a fresh rehearsal."""
    path = pathlib.Path(path)
    if not path.exists():
        return None
    kept = _load(path)
    _prove(_well_formed(kept), f"{path} is malformed (38-REVIEW DR-03)")
    _prove(
        kept["module_sha256"] == _disclosed_digests(),
        f"{path} was recorded at other {DISCLOSED_MODULES} digests: a changed driver needs a fresh "
        "rehearsal (38-REVIEW DR-02); move the old identity aside, never delete it",
    )
    return kept


def record_rehearsal(path, *, units, seconds):
    """The rehearsal identity: the first call records git_sha, the DISCLOSED_MODULES digests, its
    units (UNITS order), started_utc and its CPU seconds; a later call at the same digests adds
    its units and seconds and keeps every other key."""
    prereg = _prereg()
    path = pathlib.Path(path)
    kept = _kept_identity(path)
    if kept is None:
        identity = {
            "git_sha": git_sha(),
            "module_sha256": _disclosed_digests(),
            "units": [u for u in prereg.UNITS if u in units],
            "started_utc": _now(),
            "cpu_seconds": seconds,
        }
    else:
        identity = {
            **kept,
            "units": [u for u in prereg.UNITS if u in kept["units"] or u in units],
            "cpu_seconds": kept["cpu_seconds"] + seconds,
        }
    path.parent.mkdir(parents=True, exist_ok=True)
    phase25_run.atomic_write_json(path, identity)
    print(f"REHEARSAL {'RECORDED' if kept is None else 'KEPT'} {identity['git_sha']}", flush=True)
    return identity


# =================================================================================================
# Preflight: every refusal before the first start line (RECIPE-04, D-08, D-19, D-20, D-22)
# =================================================================================================


def stage(root):
    """2 once stage 1 is closed: on the real root THRESHOLD_FILE and the control records tracked
    and clean (D-19); on a scratch root every control record present under it. Else 1."""
    prereg = _prereg()
    controls = tuple(prereg.unit_record(u) for u in prereg.CONTROL_UNITS)
    if _is_real(root):
        return 2 if _tracked_and_clean(THRESHOLD_FILE, *controls) else 1
    return 2 if all((pathlib.Path(root) / rel).exists() for rel in controls) else 1


def p22_check():
    """D-08 / RECIPE-04: the P22 onset re-computed at every T of the grid, equal to the frozen
    P22_ONSETS and below every noised sigma, BEFORE any stage-2 training. Returns {T: onset}."""
    prereg = _prereg()
    onsets = {}
    for steps in sorted({r["steps"] for r in prereg.RECIPES}):
        onset = phase35_prereg.p22_onset_sigma(steps)
        frozen = prereg.P22_ONSETS[steps]
        _prove(
            onset == frozen,
            f"P22 onset at T={steps} is {onset}, not the frozen {frozen}: refused before any "
            "training (RECIPE-04)",
        )
        _prove(
            all(s > onset for s in prereg.NOISED_SIGMAS),
            f"P22: the grid crosses the WARNING-4/5 region at T={steps} (onset {onset}): refused "
            "before any training (RECIPE-04)",
        )
        onsets[steps] = onset
    return onsets


def _launch_requirements(*, real, device, identity, digests):
    """The real root runs on MPS after a CPU rehearsal recorded at the current driver and prereg
    digests (D-21); a scratch root is the rehearsal, on CPU."""
    if not real:
        _prove(device == "cpu", f"a rehearsal runs on CPU: pass device='cpu', not {device!r}")
        return
    _prove(device == "mps", f"E3 runs on MPS on the real root; resolved {device!r}")
    _prove(identity is not None, "the rehearsal identity is missing: run the CPU rehearsal first")
    _prove(_well_formed(identity), "the rehearsal identity is malformed (38-REVIEW DR-03)")
    _prove(
        identity["module_sha256"] == digests,
        f"{DISCLOSED_MODULES} changed after the rehearsal: rehearse the launched driver and prereg",
    )


def _launch_pathspec(root):
    """LAUNCH_PATHSPEC plus one ``:(exclude)`` per unit record that exists under ``root``: the run's
    own untracked whole-unit records (a crash relaunch, crash_rule), nothing else."""
    prereg = _prereg()
    return LAUNCH_PATHSPEC + tuple(
        ":(exclude)" + prereg.unit_record(u)
        for u in prereg.UNITS
        if (pathlib.Path(root) / prereg.unit_record(u)).exists()
    )


def _stale_outputs(unit, *, real):
    """The training sidecar, adapter and checkpoint train_stage would reuse or resume."""
    import teach_persona as tp  # torch at import: lazy

    plan = cell_plan(unit, rehearsal=not real)
    outputs = tp.arm_outputs(plan["arm"], prefix=plan["prefix"])
    return (
        phase25_points.training_sidecar(plan["point_key"]),
        outputs["adapter"],
        outputs["checkpoint"],
    )


def preflight(*, root=None, ledger_path=None, heartbeat_path=None, device=None, units=None):
    """Every refusal before the first ledger start line. Writes nothing. Returns the pf dict
    (root, real, device, ledger_path, heartbeat_path, git_sha, module_sha256, stage, pending, p22,
    gate)."""
    prereg = _prereg()
    root = pathlib.Path(root) if root is not None else pathlib.Path(_ROOT)
    real = _root_ledger(root, ledger_path, heartbeat_path)
    device = _device() if device is None else device
    _import_modules()
    launch_modules = module_sha256()
    identity_path = pathlib.Path(_ROOT) / REHEARSAL_IDENTITY
    _launch_requirements(
        real=real,
        device=device,
        identity=_load(identity_path) if real and identity_path.exists() else None,
        digests={rel: launch_modules[rel] for rel in DISCLOSED_MODULES},
    )
    if real:
        refuse_if_dirty(
            who="phase42_recipes",
            detail=(
                "every unit record publishes git_sha and hashes its modules from the working "
                "tree; a run launched from a dirty tree names a commit it cannot be regenerated "
                "from"
            ),
            pathspec=_launch_pathspec(root),
            cwd=_REPO,
        )
    launch_git_sha = git_sha()
    _prove(launch_git_sha != "unknown", "git_sha() could not read HEAD (run from the repo root)")
    lines = phase36_ledger.read_ledger(ledger_path)
    still = set(phase36_ledger.open_runs(lines)) & {prereg.run_id(u) for u in prereg.UNITS}
    for unit in prereg.UNITS:  # a reconcile here would make a finished unit unrecoverable
        _prove(
            prereg.run_id(unit) not in still or not (root / prereg.unit_record(unit)).exists(),
            f"{prereg.run_id(unit)} is open and {prereg.unit_record(unit)} exists: append its end "
            "line by command, NEVER reconcile (crash_rule)",
        )
    _prove(
        not still,
        f"the ledger holds an open attempt for {', '.join(sorted(still))} with no unit record: "
        "once the run is dead, reconcile it first: phase36_ledger.py reconcile",
    )
    current = stage(root)
    p22 = p22_check() if current == 2 else None
    pending = tuple(
        u
        for u in (prereg.CONTROL_UNITS if current == 1 else prereg.POINT_UNITS)
        if not (root / prereg.unit_record(u)).exists()
    )
    pf = {
        "root": root,
        "real": real,
        "device": device,
        "ledger_path": ledger_path,
        "heartbeat_path": heartbeat_path,
        "git_sha": launch_git_sha,
        "module_sha256": launch_modules,
        "stage": current,
        "pending": pending,
        "p22": p22,
        "gate": None,
    }
    if current == 1 and not pending:  # every control written, the threshold file not yet tracked
        print(STAGE_1_DONE, flush=True)
        return pf
    _prove(pending, f"nothing to run at stage {current}: every point record exists; emit next")
    if units is not None:
        units = tuple(units)
        _prove(
            units and units == tuple(u for u in pending if u in units),
            f"units {units!r} must be a non-empty subset of the pending stage-{current} units "
            f"{pending}, in UNITS order",
        )
        pending = units
    lost = {line["run_id"] for line in lines if line["event"] == "lost"}
    for unit in pending:
        if prereg.run_id(unit) in lost:  # crash_rule: train_stage resumes or reuses its outputs
            continue
        for path in _stale_outputs(unit, real=real):
            _prove(not path.exists(), f"{path} exists: an output of pending unit {unit}")
    gate = phase36_ledger.require_launch(FRONT, ledger_path=ledger_path)
    grid = prereg.E3_GRID_SUBSET
    phase36_caps.check_unit_caps(
        FRONT,
        **phase36_caps.counts_for("e3_grid_subset", grid),
        sigmas=len({c["sigma"] for c in grid["cells"]}),
    )
    print(
        f"PREFLIGHT OK {launch_git_sha} device={device} stage={current} pending={pending} "
        f"spent_E3_h={gate['spent_seconds'][FRONT] / 3600}"
        + (f" p22={p22}" if p22 is not None else ""),
        flush=True,
    )
    return {**pf, "pending": pending, "gate": gate}


# =================================================================================================
# The run: one ledger attempt per unit (D-22; crash_rule)
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
    """THE run: preflight, then per pending unit require_launch, ONE start line, write_unit, the end
    line naming its record. A crash inside a unit leaves an open start (reconcile -> lost). A
    scratch root given ``rehearsal_identity`` records its units and seconds into it."""
    prereg = _prereg()
    pf = preflight(
        root=root,
        ledger_path=ledger_path,
        heartbeat_path=heartbeat_path,
        device=device,
        units=units,
    )
    if rehearsal_identity is not None:  # refused BEFORE the first start line (38-REVIEW DR-02)
        _prove(not pf["real"], "the real root records no rehearsal identity")
        _kept_identity(rehearsal_identity)
    if not pf["pending"]:
        return {"stage": pf["stage"], "whole": []}
    heartbeat_path = heartbeat_path or phase36_ledger.HEARTBEAT_PATH
    started = time.monotonic()
    whole = []
    for unit in pf["pending"]:
        phase36_ledger.require_launch(FRONT, ledger_path=ledger_path)
        rid = prereg.run_id(unit)
        phase36_ledger.append("start", run_id=rid, phase=42, front=FRONT, ledger_path=ledger_path)
        state = {"point": rid, "stage": "start", "shape": None, "draw_index": None}
        # B1: the thread's first beat waits a full period: beat once now.
        phase25_run.beat(heartbeat_path, **state)
        stop, thread = phase25_run.start_heartbeat(heartbeat_path, state)
        try:
            record = write_unit(unit, pf=pf, started_utc=_now(), state=state)
        finally:
            stop.set()
            thread.join()
        phase36_ledger.append(
            "end", run_id=rid, phase=42, front=FRONT, record=record, ledger_path=ledger_path
        )
        print(f"UNIT {unit} WHOLE {record}", flush=True)
        whole.append(unit)
    if rehearsal_identity is not None:
        record_rehearsal(rehearsal_identity, units=whole, seconds=time.monotonic() - started)
    if pf["stage"] == 1 and all(
        (pf["root"] / prereg.unit_record(u)).exists() for u in prereg.CONTROL_UNITS
    ):
        print(STAGE_1_DONE, flush=True)
    print(f"RUN DONE whole={whole}", flush=True)
    return {"stage": pf["stage"], "whole": whole}
