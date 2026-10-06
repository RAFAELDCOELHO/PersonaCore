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

import collections.abc
import datetime
import gc
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import phase25_run  # noqa: E402  — atomic_write_json, beat, start_heartbeat (torch-free)
import phase36_caps  # noqa: E402  (torch-free; the launch caps)
import phase36_ledger  # noqa: E402  (torch-free; the per-seed attempt)

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402

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


# =================================================================================================
# The A2 wrapper, the D-07 comparison and the D-13 scorer
# =================================================================================================


def score_a2(group, seed, adapter_path, *, root, device):
    """NOISE-01 / D-09: the pinned A2 pass (``phase19_erasure.run_erasure_arm`` at
    ``phase40_prereg.A2_LABEL``, parity asserted by the pin) on one adapter, into the write-once
    record ``root``/``phase40_prereg.a2_record(group, seed)``. The dialogue PPL is that record's."""
    import phase19_erasure as pin  # torch at import: lazy

    prereg = _prereg()
    rel = prereg.a2_record(group, seed)
    record = pathlib.Path(root) / rel
    _prove(not record.exists(), f"{record} exists: the A2 records are write-once")
    pin.run_erasure_arm(prereg.A2_LABEL, device, adapter_path=adapter_path, record_path=record)
    _release()
    return {"group": group, "seed": seed, "record": rel, "record_sha256": _sha256(record)}


def adapter_identity(new_path, committed_path):
    """D-07 (amended): two adapters compared tensor by tensor (torch.equal, per-key max abs diff)
    plus the key set and every non-tensor top-level key. Never the file digest: torch.save writes
    the file name into the archive, so identical adapters under two names differ by it."""
    import torch

    from personacore.checkpoint import load_adapter

    a, b = load_adapter(new_path), load_adapter(committed_path)
    ta, tb = a["adapter"], b["adapter"]
    keys_equal = sorted(ta) == sorted(tb)
    n_equal = 0
    max_abs_diff = {}
    for key in sorted(set(ta) & set(tb)):
        x, y = ta[key].cpu(), tb[key].cpu()
        same_shape = x.shape == y.shape
        n_equal += same_shape and x.dtype == y.dtype and torch.equal(x, y)
        max_abs_diff[key] = (
            float((x.float() - y.float()).abs().max()) if same_shape and x.numel() else None
        )
    n_tensors = len(set(ta) | set(tb))
    metadata_keys = sorted((set(a) | set(b)) - {"adapter"})
    metadata_equal = all(a.get(k) == b.get(k) for k in metadata_keys)
    return {
        "keys_equal": keys_equal,
        "n_tensors": n_tensors,
        "n_equal": n_equal,
        "tensors_identical": keys_equal and n_equal == n_tensors and metadata_equal,
        "metadata_keys": metadata_keys,
        "metadata_equal": metadata_equal,
        "max_abs_diff": max_abs_diff,
        "comparison": "torch.equal per tensor + metadata; never the file sha256 (D-07 amended)",
        "criterion": False,
    }


def d13_scores(adapter_path, a2_record_path, device, state):
    """D-13 on one M2 adapter, only when Rafael approved it: the anchor curve, the anchor gate
    against the A2 record's exposure rank, and R_q over the pet_name questions, through the
    imported Phase 38 / 39 instruments. Returns ``phase40_prereg.d13_block`` (a measured block or
    the d13_not_measured block it returns, ruling c) plus ``n_nlls``. It catches nothing: run()
    owns ruling c's catch (plan 06)."""
    prereg = _prereg()
    _prove(prereg.D13_INCLUDED, "D-13 was not approved: d13_scores never runs")
    import phase14_recall  # torch at import: lazy
    import phase18_extraction  # same
    import phase19_erasure as pin  # same
    import phase35_prereg
    import phase38_prereg
    import phase38_rank
    import phase39_ctx
    import phase39_prereg

    slot = pin.TARGET_SLOT
    plan = phase38_rank.scoring_plan(slots=(slot,))[slot]
    taught = plan["taught"]
    a2 = json.loads(pathlib.Path(a2_record_path).read_text(encoding="utf-8"))
    a2_rank = next((row["rank"] for row in a2["exposure"] if row["slot"] == slot), None)
    refs = phase18_extraction.reference_set_for(slot)
    minted_members = phase39_prereg.minted_members(slot)
    entries = [e for e in phase35_prereg.a2_corpus_entries() if e["slot"] == slot]
    model, _cfg, tok, _forbid, _artifact = phase14_recall.load_adapted_model(
        device, adapter_path=adapter_path
    )
    try:
        anchor = phase38_rank.score_values(
            model, tok, device, slot, [taught] + plan["minted"], state
        )
        curve = phase38_rank.curve_for(taught, anchor[0], plan["minted"], anchor[1:], plan["sizes"])
        gate_nll = dict(zip(refs, phase38_rank.score_values(model, tok, device, slot, refs, state)))
        gate_rank = phase38_prereg.rank_in_prefix(
            gate_nll, taught, [r for r in refs if r != taught]
        )
        n_nlls = len(anchor) + len(gate_nll)
        committed_ranks, minted_ranks = [], []
        for entry in entries:
            rows = phase39_ctx.score_question(
                model, tok, device, entry, refs, taught=taught, state=state
            )
            minted = phase39_ctx.score_question(
                model, tok, device, entry, minted_members, taught=taught, state=state
            )
            n_nlls += len(rows) + len(minted)
            committed_ranks.append(phase39_ctx.rank_rows(rows, taught))
            minted_ranks.append(phase39_ctx.rank_rows({taught: rows[taught], **minted}, taught))
    finally:
        model = None
        _release()
    _prove(
        n_nlls == prereg.D13_NLLS_PER_ADAPTER,
        f"D-13 scored {n_nlls} NLLs, not D13_NLLS_PER_ADAPTER = {prereg.D13_NLLS_PER_ADAPTER}",
    )
    block = prereg.d13_block(
        curve=curve,
        gate_rank=gate_rank,
        a2_rank=a2_rank,
        committed_ranks=committed_ranks,
        minted_ranks=minted_ranks,
    )
    return {**block, "n_nlls": n_nlls}


# =================================================================================================
# The rehearsal identity and its disclosure (the phase39_ctx shape)
# =================================================================================================

_IDENTITY_KEYS = frozenset({"git_sha", "module_sha256", "seeds", "started_utc"})


def _load(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def rehearsal_identity_path():
    """The gitignored rehearsal identity under the output root (``_ROOT`` read at call time)."""
    return pathlib.Path(_ROOT) / "data" / "phase40_rehearsal.json"


def _kept_identity(path, *, seeds):
    """The identity already at ``path`` (None when absent), refused when it recorded a different
    seed set: a wider rehearsal would go undisclosed under it (38-REVIEW DR-02)."""
    path = pathlib.Path(path)
    if not path.exists():
        return None
    kept = _load(path)
    _prove(
        kept["seeds"] == list(seeds),
        f"{path} recorded a different seed set ({kept['seeds']}, not {list(seeds)}): a wider "
        "rehearsal would go undisclosed (38-REVIEW DR-02)",
    )
    return kept


def record_rehearsal(path, *, seeds):
    """The FIRST rehearsal attempt's identity (prereg digest included); never overwritten."""
    path = pathlib.Path(path)
    kept = _kept_identity(path, seeds=seeds)
    if kept is not None:
        print(f"REHEARSAL KEPT {kept['git_sha']}", flush=True)
        return {"status": "kept", **kept}
    identity = {
        "git_sha": git_sha(),
        "module_sha256": {rel: _sha256(_REPO / rel) for rel in DISCLOSED_MODULES},
        "seeds": list(seeds),
        "started_utc": _now(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    phase25_run.atomic_write_json(path, identity)
    print(f"REHEARSAL RECORDED {identity['git_sha']}", flush=True)
    return {"status": "recorded", **identity}


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
            f"The CPU rehearsal ran seeds {identity['seeds']} on this prereg before the MPS run; "
            f"{since} it."
        ),
        "seeds_read": identity["seeds"],
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
# R-3 b: a crashed attempt's outputs moved aside, and the re-run of its seed
# =================================================================================================


def _output_roots(seed, *, root):
    """``[(base, path)]``: every file or directory a crashed attempt of ``seed`` can leave."""
    import teach_persona as tp  # torch at import: lazy

    prereg = _prereg()
    root = pathlib.Path(root)
    rehearsal = not _is_real(root)
    found = []
    for group in prereg.GROUPS:
        paths = arm_paths(group, seed, rehearsal=rehearsal)
        for key in ("adapter", "checkpoint", "bin", "mask"):
            found.append((tp._REPO_ROOT, paths[key]))
        found.append((tp._REPO_ROOT, paths["csv"].parent))
        found.append((root, root / "data" / CSV_DIR / arm_name(group, seed, rehearsal=rehearsal)))
        found.append((root, root / prereg.a2_record(group, seed)))
    return found


def partial_outputs(seed, *, root):
    """R-3 b (c): sorted ``(rel, path)`` of every existing file a crashed attempt of ``seed`` left
    (``rel`` relative to the root it lives under). Shared by drop_attempt and emit."""
    found = []
    for base, path in _output_roots(seed, root=root):
        files = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
        found += [(_rel(f, base), f) for f in files]
    return sorted(found)


def _latest_dropped_dir(prereg, lines, seed, *, what):
    _prove(
        prereg.seed_outcomes(lines, prereg.SEEDS)[seed] == "dropped",
        f"R-3 b: seed {seed}: only a crashed attempt (closed by a lost line) is {what}, never a "
        "whole or not-run seed",
    )
    utc = prereg.lost_attempts(lines, seed)[-1]
    return utc, prereg.dropped_attempt_dir(seed, utc)


def drop_attempt(
    seed,
    *,
    cause_note,
    approved,
    head_at_dropped_attempt,
    head_change_declared=None,
    root=None,
    ledger_path=None,
):
    """R-3 b: move the latest crashed attempt's partial outputs under
    ``phase40_prereg.dropped_attempt_dir`` (never deleted) and write its write-once manifest. Run
    by Claude with ``.venv/bin/python -c`` only after Rafael's approved; never from run or main."""
    root = pathlib.Path(root) if root is not None else pathlib.Path(_ROOT)
    prereg = _prereg()
    _prove(prereg.DROPPED_SEED_RERUN, "R-3 b: DROPPED_SEED_RERUN is False: no attempt is dropped")
    lines = phase36_ledger.read_ledger(ledger_path)
    _prove(
        prereg.run_id(seed) not in phase36_ledger.open_runs(lines),
        f"seed {seed} has an open attempt: phase36_ledger.py reconcile first",
    )
    lost_utc, rel_dir = _latest_dropped_dir(prereg, lines, seed, what="dropped")
    _prove(
        not (root / prereg.seed_record(seed)).exists(),
        f"crash rule (i): {prereg.seed_record(seed)} exists; append its end line, never drop it",
    )
    _prove(not (root / rel_dir).exists(), f"{root / rel_dir} exists: write-once")
    relaunch = git_sha()
    _prove(relaunch != "unknown", "git_sha() could not read HEAD (run from the repo root)")
    outputs = partial_outputs(seed, root=root)
    manifest = {
        "seed": seed,
        "run_id": prereg.run_id(seed),
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
    failures = prereg.dropped_manifest_failures(manifest, seed=seed, lost_utc=lost_utc)
    _prove(not failures, f"R-3 b: the manifest fails: {'; '.join(failures)}")
    for (_, path), item in zip(outputs, manifest["kept"]):
        new = root / item["path"]
        new.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(new))
        _prove(_sha256(new) == item["sha256"], f"{new} changed in the move")
    for _base, path in _output_roots(seed, root=root):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()  # emptied by the moves; never rmtree
    _write_once(root / rel_dir / prereg.DROPPED_MANIFEST, manifest)
    print(f"DROPPED {seed} {rel_dir} kept={len(manifest['kept'])}", flush=True)
    return manifest


def declare_relaunch(seed, *, head_change_declared, approved, root=None, ledger_path=None):
    """R-3 b (b): declare a HEAD that moved after drop_attempt, only on Rafael's approved naming
    the move; write-once in the latest dropped attempt's directory."""
    root = pathlib.Path(root) if root is not None else pathlib.Path(_ROOT)
    prereg = _prereg()
    lines = phase36_ledger.read_ledger(ledger_path)
    _utc, rel_dir = _latest_dropped_dir(prereg, lines, seed, what="re-launched")
    path = root / rel_dir / prereg.DROPPED_MANIFEST
    _prove(path.exists(), f"R-3 b: seed {seed} has no manifest {path}: drop_attempt never ran")
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
    print(f"DECLARED {seed} {launch}", flush=True)
    return declaration


def rerun_seeds(lines, outcomes, *, root):
    """R-3: the dropped seeds a relaunch re-runs: those whose LATEST lost attempt has its
    drop_attempt manifest on disk (Rafael's approved). Without it a dropped seed is not pending."""
    prereg = _prereg()
    if not prereg.DROPPED_SEED_RERUN:
        return frozenset()
    root = pathlib.Path(root)
    return frozenset(
        seed
        for seed, outcome in outcomes.items()
        if outcome == "dropped"
        and (
            root
            / prereg.dropped_attempt_dir(seed, prereg.lost_attempts(lines, seed)[-1])
            / prereg.DROPPED_MANIFEST
        ).exists()
    )


def _dropped_attempts(seed, lines, *, root, launch_git_sha):
    """R-3 b, for a re-run seed: every lost attempt's manifest (oldest first) proved whole, every
    kept file's sha256, every relaunch declaration; the launch HEAD checked on the latest only."""
    prereg = _prereg()
    utcs = prereg.lost_attempts(lines, seed)
    attempts = []
    for utc in utcs:
        rel_dir = prereg.dropped_attempt_dir(seed, utc)
        rel = f"{rel_dir}/{prereg.DROPPED_MANIFEST}"
        _prove(
            (root / rel).exists(),
            f"R-3 b: seed {seed}'s dropped attempt {utc} has no manifest {rel}: every lost attempt "
            "of a re-run seed is listed",
        )
        manifest = _load(root / rel)
        failures = prereg.dropped_manifest_failures(manifest, seed=seed, lost_utc=utc)
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
                f"phase40_noise.declare_relaunch, never a relaunch otherwise "
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


# =================================================================================================
# Preflight: every refusal before the first start line
# =================================================================================================


def _launch_pathspec(outcomes):
    """LAUNCH_PATHSPEC plus one ``:(exclude)`` per record of a whole or dropped seed, and per
    in-process csv directory of a dropped seed: the run's own untracked outputs, nothing else
    (emit excludes the same set)."""
    import teach_persona as tp  # torch at import: lazy

    prereg = _prereg()
    excluded = []
    for seed in prereg.SEEDS:
        if outcomes.get(seed) not in ("whole", "dropped"):
            continue
        excluded.append(prereg.seed_record(seed))
        excluded += [prereg.a2_record(g, seed) for g in prereg.GROUPS]
        if outcomes[seed] == "dropped":
            excluded += [
                _rel(arm_paths(g, seed)["csv"].parent, tp._REPO_ROOT) for g in prereg.GROUPS
            ]
    return LAUNCH_PATHSPEC + tuple(":(exclude)" + rel for rel in excluded)


def preflight(*, root=None, ledger_path=None, heartbeat_path=None, device=None, seeds=None):
    """Every refusal before the first ledger start line (D-15, R-3 b). Writes nothing."""
    prereg = _prereg()
    root = pathlib.Path(root) if root is not None else pathlib.Path(_ROOT)
    real = _is_real(root)
    if real:
        _prove(
            seeds is None and ledger_path is None and heartbeat_path is None,
            "the real root runs every seed of SEEDS into the milestone ledger and heartbeat; a "
            "seeds subset or an explicit ledger / heartbeat is a rehearsal into a tmp root outside "
            "the repository",
        )
        chosen = prereg.SEEDS
    else:
        chosen = tuple(seeds) if seeds is not None else ()
        _prove(
            chosen and list(chosen) == [s for s in prereg.SEEDS if s in chosen],
            f"a rehearsal names its seeds: a non-empty subset of SEEDS {prereg.SEEDS} in order, "
            f"not {seeds!r}",
        )
        milestone = {
            (phase36_ledger._ROOT / phase36_ledger.LEDGER_PATH).resolve(),
            pathlib.Path(phase36_ledger.HEARTBEAT_PATH).resolve(),
        }
        _prove(
            ledger_path is not None and heartbeat_path is not None,
            "a rehearsal root needs an explicit ledger_path and heartbeat_path (38-REVIEW DR-01)",
        )
        _prove(
            {
                pathlib.Path(ledger_path).resolve(),
                pathlib.Path(heartbeat_path).resolve(),
            }.isdisjoint(milestone),
            "a rehearsal root writes its own ledger and heartbeat, never the milestone ones "
            "(38-REVIEW DR-01)",
        )
        _prove(device == "cpu", f"a rehearsal runs on CPU: pass device='cpu', not {device!r}")
    launch_git_sha = git_sha()
    _prove(launch_git_sha != "unknown", "git_sha() could not read HEAD (run from the repo root)")
    launch_modules = module_sha256()
    for path in run_inputs():
        _prove(
            pathlib.Path(path).exists(),
            f"{path} is missing: the run reads it, so this refuses before the ledger start line",
        )
    lines = phase36_ledger.read_ledger(ledger_path)
    still = set(phase36_ledger.open_runs(lines)) & {prereg.run_id(s) for s in prereg.SEEDS}
    _prove(
        not still,
        f"the ledger holds an open attempt for {', '.join(sorted(still))}: end it, or once the run "
        "is dead phase36_ledger.py reconcile first",
    )
    outcomes = prereg.seed_outcomes(lines, chosen)
    rerun = rerun_seeds(lines, outcomes, root=root)
    pending = prereg.pending_seeds(outcomes, rerun)
    _prove(
        pending, f"nothing to run: every seed of {list(chosen)} is whole or dropped ({outcomes})"
    )
    refuse_if_dirty(
        who="phase40_noise",
        detail=(
            "every seed record publishes git_sha and hashes its modules from the working tree; a "
            "run launched from a dirty tree names a commit it cannot be regenerated from"
        ),
        pathspec=_launch_pathspec(outcomes) if real else LAUNCH_PATHSPEC,
        cwd=_REPO,
    )
    rehearsal = not real
    for seed in pending:
        for group in prereg.GROUPS:
            paths = arm_paths(group, seed, rehearsal=rehearsal)
            arm = arm_name(group, seed, rehearsal=rehearsal)
            for path in (
                paths["adapter"],
                paths["checkpoint"],
                paths["bin"],
                paths["mask"],
                paths["csv"],
                root / "data" / CSV_DIR / arm / "run.csv",
                root / prereg.a2_record(group, seed),
            ):
                _prove(not path.exists(), f"{path} exists: an output of pending seed {seed}")
        record = root / prereg.seed_record(seed)
        _prove(not record.exists(), f"{record} exists: an output of pending seed {seed}")
    dropped_attempts = {
        seed: _dropped_attempts(seed, lines, root=root, launch_git_sha=launch_git_sha)
        for seed in pending
        if seed in rerun
    }
    gate = phase36_ledger.require_launch(FRONT, ledger_path=ledger_path)
    phase36_caps.check_unit_caps(FRONT, adapters=len(prereg.GROUPS), seeds=len(prereg.SEEDS))
    device = _device() if device is None else device
    if real:
        _prove(device == "mps", f"E2 runs on MPS on the real root; resolved {device!r}")
        path = rehearsal_identity_path()
        _prove(
            path.exists(),
            f"the rehearsal identity {path} is missing: run the CPU rehearsal first",
        )
        identity = _load(path)
        _prove(
            isinstance(identity, dict)
            and set(identity) == _IDENTITY_KEYS
            and isinstance(identity["module_sha256"], dict)
            and set(identity["module_sha256"]) == set(DISCLOSED_MODULES),
            f"{path} is malformed (38-REVIEW DR-03)",
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
    print(
        f"PREFLIGHT OK {launch_git_sha} device={device} "
        f"pending={','.join(map(str, pending))} d13={prereg.D13_INCLUDED} "
        f"projection_h={prereg.E2_PROJECTION_HOURS!r} stop_h={prereg.E2_STOP_HOURS!r} "
        f"spent_E2_s={gate['spent_seconds'][FRONT]}",
        flush=True,
    )
    return {
        "root": root,
        "pending": pending,
        "launch_git_sha": launch_git_sha,
        "launch_modules": launch_modules,
        "device": device,
        "gate": gate,
        "rehearsal_disclosure": disclosure,
        "dropped_attempts": dropped_attempts,
    }


# =================================================================================================
# The run: one ledger attempt per seed, each seed a whole unit (D-15)
# =================================================================================================


def run(
    *,
    root=None,
    ledger_path=None,
    heartbeat_path=None,
    device=None,
    seeds=None,
    rehearsal_identity=None,
):
    """THE run (D-15): preflight, then per pending seed in SEEDS order require_launch, ONE start
    line, train full, train M2, A2 full, A2 M2, D-13 last (if approved; ruling c), the write-once
    seed record, the end line naming it. A crash inside a seed leaves an open start (reconcile ->
    lost). No in-run timer and no second rule: the committed stop is require_launch's."""
    import torch

    prereg = _prereg()
    root = pathlib.Path(root) if root is not None else pathlib.Path(_ROOT)
    pf = preflight(
        root=root,
        ledger_path=ledger_path,
        heartbeat_path=heartbeat_path,
        device=device,
        seeds=seeds,
    )
    heartbeat_path = heartbeat_path or phase36_ledger.HEARTBEAT_PATH
    rehearsal = not _is_real(root)
    if rehearsal:  # 38-REVIEW DR-02: refused BEFORE the first start line
        _prove(
            rehearsal_identity is not None,
            "a rehearsal root records its identity: pass rehearsal_identity (a tmp path)",
        )
        _kept_identity(rehearsal_identity, seeds=seeds)
    else:
        _prove(rehearsal_identity is None, "the real root records no rehearsal identity")
    whole = []
    for i, seed in enumerate(pf["pending"]):
        phase36_ledger.require_launch(FRONT, ledger_path=ledger_path)
        rid = prereg.run_id(seed)
        phase36_ledger.append("start", run_id=rid, phase=40, front=FRONT, ledger_path=ledger_path)
        if rehearsal and i == 0:  # after the first start line, before the first training call
            record_rehearsal(rehearsal_identity, seeds=seeds)
        state = {"point": rid, "stage": "start", "shape": None, "draw_index": None}
        # B1: the thread's first beat waits a full period: beat once now.
        phase25_run.beat(heartbeat_path, **state)
        stop, thread = phase25_run.start_heartbeat(heartbeat_path, state)
        started_utc = _now()
        try:
            trained = {}
            for group in prereg.GROUPS:
                state.update(stage=f"train_{group}")
                trained[group] = train_adapter(group, seed, root=root, rehearsal=rehearsal)
            adapters = {
                group: arm_paths(group, seed, rehearsal=rehearsal)["adapter"]
                for group in prereg.GROUPS
            }
            a2 = {}
            for group in prereg.GROUPS:
                state.update(stage=f"a2_{group}")
                a2[group] = score_a2(group, seed, adapters[group], root=root, device=pf["device"])
            d13 = None
            if prereg.D13_INCLUDED:
                state.update(stage="d13")
                # Ruling c: every exception of THIS call (SystemExit included: the prereg's
                # refusal type; never KeyboardInterrupt) and every non-conforming return becomes
                # d13_not_measured, and the seed finishes. Nothing after it may fail on the return.
                try:
                    raw = d13_scores(
                        adapters["m2"], root / prereg.a2_record("m2", seed), pf["device"], state
                    )
                except (Exception, SystemExit) as exc:
                    _release()
                    d13 = prereg.d13_not_measured("exception", f"{type(exc).__name__}: {exc}")
                else:
                    defect = None
                    if (
                        not isinstance(raw, collections.abc.Mapping)
                        or type(raw.get("measured")) is not bool
                    ):
                        defect = "no bool 'measured'"
                    elif not raw["measured"] and not (
                        raw.get("failure_kind") in prereg.D13_FAILURE_KINDS
                        and isinstance(raw.get("reason"), str)
                        and raw["reason"].strip()
                    ):
                        defect = "measured False without a D13_FAILURE_KINDS failure_kind + reason"
                    else:
                        try:
                            json.dumps(raw, sort_keys=True)  # atomic_write_json's options
                        except (TypeError, ValueError) as exc:
                            defect = f"not JSON-serialisable ({type(exc).__name__}: {exc})"
                    d13 = raw
                    if defect is not None:
                        d13 = prereg.d13_not_measured(
                            "malformed_reading",
                            f"d13_scores returned a {type(raw).__name__}: {defect}",
                        )
                if not d13["measured"]:
                    print(
                        f"D13 NOT_MEASURED {seed} {d13['failure_kind']}: {d13['reason']}",
                        flush=True,
                    )
            finished_utc = _now()
            end_sha = git_sha()
            blob = {
                "front": FRONT,
                "phase": 40,
                "seed": seed,
                "run_id": rid,
                "rehearsal": rehearsal,
                "groups": {g: {**trained[g], "a2": a2[g]} for g in prereg.GROUPS},
                "d13": d13,
                "approval": prereg.approval_block(),
                "rehearsal_disclosure": pf["rehearsal_disclosure"],
                "dropped_attempts": pf["dropped_attempts"].get(seed, []),
                "provenance": {
                    "run": {
                        "git_sha_at_launch": pf["launch_git_sha"],
                        "git_sha_at_end": end_sha,
                        "head_moved_during_run": end_sha != pf["launch_git_sha"],
                        "device": pf["device"],
                        "torch_version": torch.__version__,
                        "started_utc": started_utc,
                        "finished_utc": finished_utc,
                    },
                    "module_sha256_at_launch": pf["launch_modules"],
                },
            }
            _write_once(root / prereg.seed_record(seed), blob)
            state.update(stage="done")
        finally:
            stop.set()
            thread.join()
        phase36_ledger.append(
            "end",
            run_id=rid,
            phase=40,
            front=FRONT,
            record=prereg.seed_record(seed),
            ledger_path=ledger_path,
        )
        hours = (
            datetime.datetime.fromisoformat(finished_utc)
            - datetime.datetime.fromisoformat(started_utc)
        ).total_seconds() / 3600
        print(f"SEED {seed} WHOLE {hours:.4f}", flush=True)
        whole.append(seed)
    print(f"RUN DONE whole={whole}", flush=True)
    return whole
