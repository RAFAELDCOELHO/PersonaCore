"""Phase 40 E2 (NOISE-01) — the M2 seed noise floor: S seeds x {full, M2}, each A2-scored.

    .venv/bin/python scripts/phase40_noise.py preflight   # every refusal, writes nothing
    .venv/bin/python scripts/phase40_noise.py run         # the seeds: one ledger attempt each
    .venv/bin/python scripts/phase40_noise.py emit        # CPU: the noise-floor record
    .venv/bin/python scripts/phase40_noise.py report      # the report rendered from the record

THE PER-SEED UNIT (D-15). For each seed of ``phase40_prereg.SEEDS``, in this order: train the full
adapter, train the M2 adapter, the A2 pass on the full adapter, the A2 pass on the M2 adapter, and
D-13 last, only when Rafael approved it (``phase40_prereg.D13_INCLUDED``). Training is the pinned
teaching recipe through ONE helper, ``train_adapter`` (full = the ``real`` arm's spec, M2 = the
Phase 19 retrain spec minus exactly the pet_name fact), under arm names that can never be ``real``
or a published adapter. Scoring is the pinned ``phase19_erasure.run_erasure_arm`` at
``phase40_prereg.A2_LABEL`` with an explicit record path (``score_a2``). D-07 compares adapters
tensor by tensor (``adapter_identity``), never by file digest: ``torch.save`` writes the file
name into the archive, so two identical adapters saved under two names differ by sha256.

ONE LEDGER ATTEMPT PER SEED, under ``require_launch("E2")``. A crash mid-seed drops that seed's
attempt (it re-runs only under Rafael's R-3 ruling, as a new attempt). A D-13 failure never drops
a seed (ruling c, 2026-10-06): the seed record carries ``d13_not_measured`` and the seed finishes.

It is launched only through artifacts/com.personacore.phase40.e2.plist, after Rafael's "approved".
Torch-free at import only: preflight, run and emit load torch (every torch-importing module and
the pre-registration are imported inside the functions that need them).
"""

import datetime
import gc
import hashlib
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import phase25_run  # noqa: E402  — atomic_write_json, beat, start_heartbeat (torch-free)
import phase36_caps  # noqa: E402,F401  (torch-free; the run loop's caps, plan 06)
import phase36_ledger  # noqa: E402,F401  (torch-free; the per-seed attempt, plan 06)

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402,F401

# FIXED: the cwd of every git call and the base of the module digests.
_REPO = pathlib.Path(__file__).resolve().parent.parent
# The default OUTPUT root (results/, data/) and the identity that selects the real-root branches.
_ROOT = _REPO
FRONT = "E2"
LAUNCH_PATHSPEC = ("scripts", "src", "results", "artifacts")
PREREG_FILE = "scripts/phase40_prereg.py"
DRIVER_FILE = "scripts/phase40_noise.py"
DISCLOSED_MODULES = (DRIVER_FILE, PREREG_FILE)
MODULES = DISCLOSED_MODULES + (
    "scripts/teach_persona.py",
    "scripts/phase19_erasure.py",
    "scripts/phase19_run.py",
    "scripts/phase14_recall.py",
    "scripts/phase18_extraction.py",
    "scripts/phase14_factset.py",
    "scripts/phase35_prereg.py",
    "scripts/phase36_ledger.py",
    "scripts/phase36_caps.py",
    "scripts/phase25_run.py",
    "scripts/phase38_rank.py",
    "scripts/phase38_prereg.py",
    "scripts/phase39_ctx.py",
    "scripts/phase39_prereg.py",
    "scripts/phase37_prereg.py",
    "src/personacore/training/loop.py",
    "src/personacore/checkpoint.py",
    "src/personacore/lora/config.py",
    "src/personacore/lora/inject.py",
    "src/personacore/lora/layer.py",
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
ARM_PREFIX = "phase40"
# Does not match results/phase40_*: a rehearsal csv never lands under the record glob.
REHEARSAL_PREFIX = "phase40rh"
CSV_DIR = "phase40_e2"


def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[phase40_noise] {message}")


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


def _is_real(root):
    """The real root, or any root inside the repository."""
    resolved = pathlib.Path(root).resolve()
    return resolved == pathlib.Path(_ROOT).resolve() or resolved.is_relative_to(_REPO.resolve())


def _prereg():
    """phase40_prereg, imported lazily (torch at import through phase35_prereg.seed_list)."""
    import phase40_prereg

    return phase40_prereg


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


# =================================================================================================
# Arm names and specs
# =================================================================================================


def arm_name(group, seed, *, rehearsal=False):
    """``e2_<group>_seed<seed>`` (``e2rh_`` for the rehearsal): never ``real`` (the shippable
    persona_adapter.pt), never a published arm name."""
    groups = _prereg().GROUPS
    _prove(group in groups, f"group {group!r} is not one of {groups}")
    return f"{'e2rh' if rehearsal else 'e2'}_{group}_seed{seed}"


def arm_paths(group, seed, *, rehearsal=False):
    """teach_persona's write targets for one arm, under the phase40 / phase40rh prefix."""
    import teach_persona as tp  # torch at import: lazy

    prefix = REHEARSAL_PREFIX if rehearsal else ARM_PREFIX
    return tp.arm_outputs(arm_name(group, seed, rehearsal=rehearsal), prefix=prefix)


def _target_fact_id():
    import phase14_factset
    import phase19_erasure as pin  # torch at import: lazy

    return next(f.id for f in phase14_factset.LOCKED_FACTS if f.slot == pin.TARGET_SLOT)


def arm_spec(group):
    """``(facts, second_person, replay_ratio)``: full = the ``real`` arm; M2 = the Phase 19
    retrain spec, proved to drop exactly the pet_name fact and keep both settings."""
    import phase19_erasure as pin  # torch at import: lazy
    import teach_persona as tp  # same

    groups = _prereg().GROUPS
    _prove(group in groups, f"group {group!r} is not one of {groups}")
    real = tp.arm_spec("real")
    if group == "full":
        return real
    target = _target_fact_id()
    facts, second_person, replay_ratio = pin.retrain_arm_spec(target)
    dropped = sorted({f.id for f in real[0]} - {f.id for f in facts})
    _prove(
        dropped == [target] and len(facts) == len(real[0]) - 1,
        f"the M2 spec dropped {dropped}, not exactly [{target!r}]",
    )
    _prove(
        (second_person, replay_ratio) == real[1:],
        "the M2 spec changed second_person / replay_ratio against the real arm",
    )
    return facts, second_person, replay_ratio


# =================================================================================================
# Inputs and comparators
# =================================================================================================


def comparators():
    """D-07 / D-08: the committed adapters a new adapter is compared with, from the constants that
    wrote them: the Phase 19 M2 retrain, the shippable full adapter, and the two Phase 19
    dialogue-floor (full recipe) adapters."""
    import phase14_recall as recall  # torch at import: lazy
    import phase19_erasure as pin  # same
    import phase38_rank
    import teach_persona as tp  # same

    floor = {
        seed: tp.arm_outputs(f"{pin.DIALOGUE_FLOOR_ARM}_seed{seed}", prefix=pin.RETRAIN_PREFIX)[
            "adapter"
        ]
        for seed in pin.DIALOGUE_NOISE_FLOOR_SEEDS
    }
    return {
        "m2_seed1337": phase38_rank.m2_adapter_path(),
        "full_seed1337": recall.ADAPTER_PATH,
        "full_seed2024": floor[2024],
        "dialogue_floor_seed1337": floor[1337],
    }


def run_inputs():
    """Every input file the run reads, from the constants its readers take them from:
    `refuse_if_dirty` cannot see the gitignored ones, so a missing one must refuse before the
    ledger start line."""
    import phase14_recall as recall  # torch at import: lazy
    import phase19_erasure as pin  # same
    import teach_persona as tp  # same

    inputs = (
        tp.CONVBASE_BEST,  # train_arm's base
        tp.TOKENIZER_PATH,
        tp.DIALOG_TRAIN_BIN,  # replay source
        tp.DIALOG_TRAIN_MASK,
        tp.DIALOG_VAL_BIN,  # the adapter-on/off PPL pair and the A2 dialogue PPL
        tp.DIALOG_VAL_MASK,
        recall.CONVBASE_SLIM,  # load_adapted_model
        recall.ADAPTER_PATH,  # the production adapter, proved unchanged around each train
        recall.TOKENIZER_PATH,
        pin.RETENTION_BIN,  # run_erasure_arm's retention perplexity
        pin.PHASE18_CORPUS_PATH,  # run_erasure_arm's corpus
        pin.PHASE18_ARM_RECORD_PATH,  # run_erasure_arm's pre-erasure record
        *comparators().values(),
    )
    if _prereg().D13_INCLUDED:
        import phase38_prereg

        inputs += ((_REPO / phase38_prereg.MINTING_RECORD).resolve(),)
    return inputs


# =================================================================================================
# The ONE training helper
# =================================================================================================


def train_adapter(group, seed, *, root, rehearsal=False):
    """Train one adapter with the pinned recipe; the driver's ONE call of teach_persona's arm
    trainer (registered in tests/test_phase23_resume.py; no resume_from). The csv it writes under
    results/ moves under ``root``/data/phase40_e2/<arm>/ and the emptied directory is removed; the
    shippable persona_adapter.pt is proved byte-unchanged around the call."""
    import phase14_factset
    import phase14_recall as recall  # torch at import: lazy
    import teach_persona as tp  # same

    root = pathlib.Path(root)
    arm = arm_name(group, seed, rehearsal=rehearsal)
    prefix = REHEARSAL_PREFIX if rehearsal else ARM_PREFIX
    paths = arm_paths(group, seed, rehearsal=rehearsal)
    csv_dst = root / "data" / CSV_DIR / arm / "run.csv"
    for path in (paths["adapter"], paths["checkpoint"], paths["bin"], paths["mask"], csv_dst):
        _prove(not path.exists(), f"{path} exists: stale output. Move it in a reviewed step")
    facts, second_person, replay_ratio = arm_spec(group)
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
    paths["csv"].parent.rmdir()  # empty after the move; anything else left there refuses
    _prove(
        _sha256(recall.ADAPTER_PATH) == production,
        f"{recall.ADAPTER_PATH} (persona_adapter.pt) changed during training",
    )
    return {
        "group": group,
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
