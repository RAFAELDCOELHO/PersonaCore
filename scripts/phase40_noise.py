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
import os
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


def _root_ledger(root, *paths):
    """WR-02: the ONE root/ledger pairing (preflight, emit, drop_attempt, declare_relaunch);
    ``paths`` are the explicit ledger (and preflight's heartbeat). The real root reads and writes
    the milestone ones only; a tmp root its own explicit ones, never the milestone ones
    (38-REVIEW DR-01). Returns whether ``root`` is real."""
    if _is_real(root):
        _prove(
            all(p is None for p in paths),
            "the real root runs every seed of SEEDS into the milestone ledger and heartbeat; an "
            "explicit ledger / heartbeat is a rehearsal into a tmp root outside the repository",
        )
        return True
    _prove(
        all(p is not None for p in paths),
        "a rehearsal root needs an explicit ledger_path and heartbeat_path (38-REVIEW DR-01; "
        "emit, drop_attempt and declare_relaunch take the ledger only)",
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
    _root_ledger(root, ledger_path)
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
    _root_ledger(root, ledger_path)
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
    real = _root_ledger(root, ledger_path, heartbeat_path)
    if real:
        _prove(
            seeds is None,
            "the real root runs every seed of SEEDS into the milestone ledger and heartbeat; a "
            "seeds subset is a rehearsal into a tmp root outside the repository",
        )
        chosen = prereg.SEEDS
    else:
        chosen = tuple(seeds) if seeds is not None else ()
        _prove(
            chosen and list(chosen) == [s for s in prereg.SEEDS if s in chosen],
            f"a rehearsal names its seeds: a non-empty subset of SEEDS {prereg.SEEDS} in order, "
            f"not {seeds!r}",
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
    for seed in prereg.SEEDS:  # WR-01: a reconcile here would make the seed unrecoverable
        _prove(
            prereg.run_id(seed) not in still or not (root / prereg.seed_record(seed)).exists(),
            f"{prereg.run_id(seed)} is open and {prereg.seed_record(seed)} exists: crash rule (i) "
            "— append its end line by command (40-09 Task 4 step 2 (i)), NEVER reconcile (a lost "
            "line makes this finished seed unrecoverable)",
        )
    _prove(
        not still,
        f"the ledger holds an open attempt for {', '.join(sorted(still))} with no seed record: "
        "once the run is dead, phase36_ledger.py reconcile first",
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


# =================================================================================================
# The noise-floor record (CPU): built from the seed and A2 records through the frozen prereg only
# =================================================================================================

NOT_PRODUCED = "not produced by the dropped attempt"


def _not_whole(outcomes, *seeds):
    """None when every seed is whole, else the reason the first one is not (never a KeyError)."""
    for seed in seeds:
        if outcomes[seed] != "whole":
            return f"not whole: seed {seed} is {outcomes[seed]}"
    return None


def _verified_kept(manifest, *, root, what):
    """Every kept file of a dropped attempt re-hashed at its path under ``root``."""
    for item in manifest["kept"]:
        kept = root / item["path"]
        _prove(
            kept.is_file() and _sha256(kept) == item["sha256"],
            f"R-3 b: {what}: kept file {item['path']} is missing or its sha256 changed",
        )


def _listed_attempts(sr, seed, lines, *, root):
    """R-3 b (c, d), a whole seed's lost attempts as its seed record lists them: each manifest and
    relaunch declaration by sha256, each kept file re-hashed, and per group the new adapter against
    the dropped attempt's kept one, tensor by tensor."""
    import teach_persona as tp  # torch at import: lazy

    prereg = _prereg()
    lost = prereg.lost_attempts(lines, seed)
    listed = sr["dropped_attempts"]
    for attempt in listed:
        _prove(
            attempt["lost_utc"] in lost,
            f"R-3 b: seed {seed}'s record names a lost attempt the ledger lacks "
            f"({attempt['lost_utc']})",
        )
    _prove(
        [a["lost_utc"] for a in listed] == lost,
        f"R-3 b (c): every lost attempt of a whole seed is listed in its seed record (seed {seed}: "
        f"ledger {lost})",
    )
    attempts = []
    for attempt in listed:
        _prove(
            _sha256(root / attempt["manifest"]) == attempt["manifest_sha256"],
            f"R-3 b: {attempt['manifest']}'s sha256 differs from seed {seed}'s manifest_sha256",
        )
        for declaration in attempt["relaunch_declarations"]:
            _prove(
                _sha256(root / declaration["path"]) == declaration["sha256"],
                f"R-3 b: {declaration['path']}'s sha256 differs from seed {seed}'s record",
            )
        _verified_kept(attempt, root=root, what=f"seed {seed}")
        identity = {}
        for group in prereg.GROUPS:
            new = sr["groups"][group]["adapter"]
            item = next((i for i in attempt["kept"] if i["from"] == new), None)
            identity[group] = (
                NOT_PRODUCED
                if item is None
                else adapter_identity(tp._REPO_ROOT / new, root / item["path"])
            )
        attempts.append({**attempt, "kept_verified": True, "adapter_identity": identity})
    return attempts


def _left_dropped(seed, lines, *, root):
    """R-3 b (c) for a seed no relaunch re-ran: each manifest found for its lost attempts
    (re-hashed) and each partial output still in place."""
    prereg = _prereg()
    manifests = []
    for utc in prereg.lost_attempts(lines, seed):
        rel = f"{prereg.dropped_attempt_dir(seed, utc)}/{prereg.DROPPED_MANIFEST}"
        if not (root / rel).exists():
            continue
        manifest = _load(root / rel)
        _verified_kept(manifest, root=root, what=f"dropped seed {seed}")
        manifests.append(
            {
                **manifest,
                "manifest": rel,
                "manifest_sha256": _sha256(root / rel),
                "kept_verified": True,
            }
        )
    return {
        "manifests": manifests,
        "in_place": [
            {"from": rel, "sha256": _sha256(path)} for rel, path in partial_outputs(seed, root=root)
        ],
    }


def build_record(root, *, ledger_path=None):
    """NOISE-01 / NOISE-02 (CPU): the noise-floor record from the whole seeds' seed and A2 records,
    each proved by sha256 first; every reduction is the frozen prereg's (recall_floor,
    gap_noise_floor, d12_table, d07_reading, d08b_reading, d13_reading)."""
    import phase19_erasure as pin  # torch at import: lazy
    import phase19_floor
    import phase19_run  # torch at import: lazy
    import phase35_prereg
    import phase37_prereg
    import teach_persona as tp  # torch at import: lazy

    prereg = _prereg()
    root = pathlib.Path(root)
    off = prereg.committed_adapter_off()
    lines = phase36_ledger.read_ledger(ledger_path)
    outcomes = prereg.seed_outcomes(lines, prereg.SEEDS)
    whole = [s for s in prereg.SEEDS if outcomes[s] == "whole"]
    srs = {seed: _load(root / prereg.seed_record(seed)) for seed in whole}
    devices = {srs[s]["provenance"]["run"]["device"] for s in whole}
    _prove(
        len(devices) <= 1,
        f"the whole seeds ran on {sorted(devices)}: one device across every whole seed (a mixed "
        "set would mix adapter-off scales)",
    )
    device = next(iter(devices), None)

    a2, rows, per_seed, dropped_attempts = {}, {g: {} for g in prereg.GROUPS}, {}, {}
    for seed in whole:
        sr = srs[seed]
        a2[seed], per_seed[seed] = {}, {}
        for group in prereg.GROUPS:
            entry = sr["groups"][group]
            rel = entry["a2"]["record"]
            _prove(
                _sha256(root / rel) == entry["a2"]["record_sha256"],
                f"{rel}'s sha256 differs from the one seed {seed}'s record names",
            )
            adapter = tp._REPO_ROOT / entry["adapter"]
            _prove(
                adapter.is_file() and _sha256(adapter) == entry["adapter_sha256"],
                f"{entry['adapter']} is missing or differs from seed {seed}'s adapter_sha256",
            )
            rec = _load(root / rel)
            _prove(
                rec["config"]["device"] == device,
                f"WR-03: {rel} was measured on {rec['config']['device']!r}, but seed {seed}'s "
                f"record ran on {device!r}",
            )
            _prove(
                rec["config"]["arm"] == prereg.A2_LABEL,
                f"ruling b: {rel} carries config.arm {rec['config']['arm']!r}, not the pinned A2 "
                f"label {prereg.A2_LABEL!r}",
            )
            a2[seed][group] = rec
            rows[group][seed] = prereg.a2_rows(rec, *prereg.a2_scope(rec))
            per_seed[seed][group] = {
                "slots": prereg.slot_rows(rows[group][seed]),
                "dialogue_ppl": rec["dialogue_ppl"],
                "pre_erasure_dialogue_ppl": rec["pre_erasure"]["dialogue_ppl"],
                "dialogue_gap": prereg.dialogue_gap(rec, off, device=rec["config"]["device"]),
                "adapter": entry["adapter"],
                "adapter_sha256": entry["adapter_sha256"],
                "a2_record": rel,
                "a2_record_sha256": entry["a2"]["record_sha256"],
                "train": entry["train"],
            }
        attempts = _listed_attempts(sr, seed, lines, root=root)
        if attempts:
            dropped_attempts[seed] = attempts
    dropped_seed_outputs = {
        seed: _left_dropped(seed, lines, root=root)
        for seed in prereg.SEEDS
        if outcomes[seed] == "dropped"
    }

    v3_sampling_floor = _load(phase19_run.NOISE_FLOORS_PATH)["nontarget_noise_floor"]["value"]
    crn = {
        "confirmation_g": prereg.CONFIRMATIONS["g"],
        "v3_sampling_floor": v3_sampling_floor,
        "source": (
            f"{phase19_run.NOISE_FLOORS_PATH.relative_to(phase19_run._REPO_ROOT).as_posix()}"
            "::nontarget_noise_floor.value"
        ),
    }
    record = {
        "front": FRONT,
        "phase": 40,
        "device": device,
        "seeds": {
            "outcomes": outcomes,
            "whole": whole,
            "dropped": [s for s in prereg.SEEDS if outcomes[s] == "dropped"],
            "not_run": [s for s in prereg.SEEDS if outcomes[s] == "not_run"],
            "dropped_attempts": dropped_attempts,
            "dropped_seed_outputs": dropped_seed_outputs,
        },
        "per_seed": per_seed,
    }
    if len(whole) >= phase35_prereg.ENTRIES["e2_min_seeds"]["value"]:
        recall = prereg.recall_floor(rows["full"], rows["m2"])
        gap = prereg.gap_noise_floor({s: per_seed[s]["full"]["dialogue_gap"]["gap"] for s in whole})
        record.update(
            status="MEASURED",
            recall_floor=recall,
            gap_noise_floor=gap["value"],
            gap_noise_floor_detail=gap,
            m2_gap_descriptive=prereg.gap_noise_floor(
                {s: per_seed[s]["m2"]["dialogue_gap"]["gap"] for s in whole}
            ),
            d12=prereg.d12_table(rows["full"], rows["m2"]),
        )
        crn["published_below_v3_sampling_floor"] = recall["published"]["value"] < v3_sampling_floor
    else:
        record.update(
            status="INSUFFICIENT_SEEDS",
            stop=(
                "INSUFFICIENT_SEEDS: fewer than e2_min_seeds whole seeds; no floor is published "
                "and the phase stops for Rafael (ruling e)"
            ),
        )

    # D-07 / D-08 / D-08b, descriptive: each entry only when the seeds it names are whole.
    comp = comparators()

    def new(group, seed):
        return tp._REPO_ROOT / srs[seed]["groups"][group]["adapter"]

    identity = {
        key: _not_whole(outcomes, seed) or adapter_identity(new(group, seed), comp[key])
        for key, group, seed in (
            ("m2_seed1337", "m2", 1337),
            ("full_seed1337", "full", 1337),
            ("full_seed2024", "full", 2024),
        )
    }
    d07 = {"m2_seed1337": _not_whole(outcomes, 1337)}
    d08b = _not_whole(outcomes, 1337)
    if d07["m2_seed1337"] is None:
        rec = a2[1337]["m2"]
        committed = _load(pin.arm_record_path("retrain"))
        d07["m2_seed1337"] = {
            **prereg.d07_reading(
                identity["m2_seed1337"]["tensors_identical"],
                rows["m2"][1337],
                prereg.a2_rows(committed, *prereg.a2_scope(rec)),
            ),
            "draw_identity": phase37_prereg.draw_identity(rec["draws"], committed["draws"]),
        }
        rec = a2[1337]["full"]
        family, tiers = prereg.a2_scope(rec)
        phase18 = _load(pin.PHASE18_ARM_RECORD_PATH)
        d08b = {
            **prereg.d08b_reading(
                identity["full_seed1337"]["tensors_identical"],
                prereg.a2_rows(phase18, family, tiers),
                rows["full"][1337],
            ),
            "draw_identity": phase37_prereg.draw_identity(
                rec["draws"], [d for d in phase18["draws"] if d["family"] == family]
            ),
        }
    d08 = {
        "statement": prereg.ENTRIES["d08_correction"]["value"],
        "persona_vs_dialogue_floor_1337": adapter_identity(
            comp["full_seed1337"], comp["dialogue_floor_seed1337"]
        ),
    }
    pair = _not_whole(outcomes, 1337, 2024)
    if pair is None:
        readings = [per_seed[s]["full"]["dialogue_gap"] for s in (1337, 2024)]
        pair = {
            "abs_gap_difference": abs(readings[0]["gap"] - readings[1]["gap"]),
            "beside": phase19_floor.DIALOGUE_PPL_NOISE_FLOOR,
            "devices": [r["device"] for r in readings],
            "rehearsal": [r["rehearsal"] for r in readings],
        }
    observed = {
        "tensor_identity": {
            key: value if isinstance(value, str) else value["tensors_identical"]
            for key, value in identity.items()
        },
        "gap_pair": pair,
        "m2_counts": d07["m2_seed1337"]
        if isinstance(d07["m2_seed1337"], str)
        else all(c["delta"] == 0 for c in d07["m2_seed1337"]["counts"].values()),
        "full_counts": d08b
        if isinstance(d08b, str)
        else all(c["delta"] == 0 for c in d08b["counts"].values()),
        "status": record["status"],
    }
    blocks = {s: srs[s]["d13"] for s in whole}
    now = module_sha256()
    record.update(
        identity=identity,
        d07=d07,
        d08=d08,
        d08b=d08b,
        d13={"reading": prereg.d13_reading(blocks), "blocks": blocks}
        if prereg.D13_INCLUDED
        else None,
        a2_label={"label": prereg.A2_LABEL, "explanation": prereg.ENTRIES["a2_pass"]["value"]},
        crn_addendum=crn,
        predictions={
            key: {"prediction": text, "observed": observed[key], "criterion": False}
            for key, text in prereg.ENTRIES["predictions"]["value"].items()
        },
        estimator=json.loads(json.dumps(prereg.E2_NOISE_FLOOR_ESTIMATOR, default=dict)),
        approval=prereg.approval_block(),
        rehearsal_disclosure={s: srs[s]["rehearsal_disclosure"] for s in whole},
        phase41_adapters={
            s: {
                g: {
                    "path": srs[s]["groups"][g]["adapter"],
                    "sha256": srs[s]["groups"][g]["adapter_sha256"],
                }
                for g in prereg.GROUPS
            }
            for s in phase35_prereg.e1_teaching_seeds()
            if s in whole
        },
        provenance={
            "seeds": {s: srs[s]["provenance"]["run"] for s in whole},
            "emit": {
                "device": "cpu",
                "head_at_write": git_sha(),
                "written_utc": _now(),
                "module_sha256": now,
                "modules_changed_since_launch": sorted(
                    rel
                    for rel in MODULES
                    if any(
                        srs[s]["provenance"]["module_sha256_at_launch"].get(rel) != now[rel]
                        for s in whole
                    )
                ),
            },
        },
    )
    return record


def emit(*, root=None, ledger_path=None):
    """Write results/phase40_noise_floor.json ONCE (CPU). On the real root, from a clean tree but
    for the run's own untracked outputs (the same pathspec preflight uses)."""
    root = pathlib.Path(root) if root is not None else pathlib.Path(_ROOT)
    real = _root_ledger(root, ledger_path)
    prereg = _prereg()
    out = root / prereg.NOISE_FLOOR_RECORD
    _prove(
        not out.exists(),
        f"{out} exists — REFUSING to overwrite it. The noise-floor record is write-once; a "
        "correction is a dated continuation via scripts/_addendum.py",
    )
    if real:
        refuse_if_dirty(
            who="phase40_noise",
            detail=(
                "the noise-floor record publishes git_sha and hashes its modules from the working "
                "tree; a record written from a dirty tree names a commit it cannot be regenerated "
                "from"
            ),
            pathspec=_launch_pathspec(
                prereg.seed_outcomes(phase36_ledger.read_ledger(ledger_path), prereg.SEEDS)
            ),
            cwd=_REPO,
        )
    record = build_record(root, ledger_path=ledger_path)
    _write_once(out, record)
    published = record["recall_floor"]["published"]["value"] if "recall_floor" in record else "-"
    gap = record.get("gap_noise_floor", "-")
    print(
        f"EMIT {record['status']} whole={','.join(map(str, record['seeds']['whole']))} "
        f"recall_floor={published!r} gap_noise_floor={gap!r}",
        flush=True,
    )
    return record


# =================================================================================================
# The report: the record rendered, nothing else (every number read from the record)
# =================================================================================================


def _table(header, rows):
    """A GFM table; a pipe inside a cell is escaped, else it would add cells."""

    def line(cells):
        return "| " + " | ".join(str(c).replace("|", "\\|") for c in cells) + " |"

    return [line(header), "|" + "---|" * len(header), *(line(row) for row in rows), ""]


def _seed_order(keys):
    """The record's seeds (JSON str keys) in SEEDS order, never key order."""
    return [str(s) for s in _prereg().SEEDS if str(s) in keys]


def _slot_order(keys):
    """The record's slots in GATED_NONTARGET_SLOTS order, then the target."""
    import phase19_erasure as pin  # torch at import: lazy

    return [s for s in (*pin.GATED_NONTARGET_SLOTS, pin.TARGET_SLOT) if s in keys]


def _seeds_text(seeds):
    return ", ".join(map(str, seeds)) or "none"


def _attempt_lines(attempt, launch_git_sha):
    """R-3 b: one dropped attempt's manifest, its kept files and relaunch declarations."""
    beside = f" beside the seed's git_sha_at_launch `{launch_git_sha}`" if launch_git_sha else ""
    lines = [
        f"- lost line utc: {attempt['lost_utc']}",
        f"- cause note: {attempt['cause_note']}",
        f"- Rafael's approved: {attempt['approved']}",
        f"- HEAD at the dropped attempt: `{attempt['head_at_dropped_attempt']}`{beside}",
        f"- declared change: {attempt['head_change_declared'] or 'none'}",
        f"- manifest: `{attempt['manifest']}` sha256 `{attempt['manifest_sha256']}`",
        "",
        *_table(
            ("kept from", "kept at", "sha256"),
            [[i["from"], i["path"], i["sha256"]] for i in attempt["kept"]],
        ),
    ]
    for d in attempt.get("relaunch_declarations", []):
        lines.append(
            f"- relaunch declaration `{d['path']}` sha256 `{d['sha256']}`: launch "
            f"`{d['launch_git_sha']}`, declared change {d['head_change_declared']}, approved "
            f"{d['approved']}"
        )
    return [*lines, ""]


def _disclosure_lines(seed, disclosure):
    if disclosure.get("this_is_the_rehearsal"):
        return [f"Seed {seed}: this is the rehearsal.", ""]
    changed = [rel for rel, flag in disclosure["changed"].items() if flag]
    commits = [
        f"- `{c['sha']}` {c['reason']} (touched: {', '.join(c['modules'])})"
        for c in disclosure["commits"]
    ]
    return [
        f"Seed {seed}: {disclosure['statement']}",
        f"- rehearsal git sha `{disclosure['rehearsal_git_sha']}`, launch git sha "
        f"`{disclosure['launch_git_sha']}`",
        f"- changed modules: {', '.join(changed) or 'none'}",
        *(commits or ["- no commit touched a disclosed module since the rehearsal"]),
        "",
    ]


def _identity_text(value):
    if isinstance(value, str):
        return value
    return (
        f"tensors_identical {value['tensors_identical']} ({value.get('n_equal')}/"
        f"{value.get('n_tensors')} tensors equal, tensor by tensor)"
    )


def _counts_table(counts):
    return _table(
        ("slot", "new", "committed", "delta"),
        [
            [slot, "/".join(map(str, c["new"])), "/".join(map(str, c["committed"])), c["delta"]]
            for slot in _slot_order(counts)
            for c in (counts[slot],)
        ],
    )


def _draws_text(identity):
    return (
        f"draw identity: bit_identical {identity['bit_identical']}, "
        f"{identity['differing_completions']}/{identity['n_completions']} completions and "
        f"{identity['differing_entries']}/{identity['n_entries']} entries differ"
    )


def render_report(record):
    """The noise-floor report, rendered from the record only (pure; returns the markdown)."""
    record = json.loads(json.dumps(record, sort_keys=True))  # one key type: the file's
    groups = _prereg().GROUPS
    measured = record["status"] == "MEASURED"
    seeds, per_seed = record["seeds"], record["per_seed"]
    out = ["# Phase 40 — E2 training-seed noise floor", ""]

    out += [
        "## Status",
        "",
        f"Status: **{record['status']}**; device {record['device']}; whole seeds "
        f"{_seeds_text(seeds['whole'])}; dropped {_seeds_text(seeds['dropped'])}; not run "
        f"{_seeds_text(seeds['not_run'])}.",
        "",
    ]
    if "stop" in record:
        out += [record["stop"], ""]

    a = record["approval"]
    out += [
        "## Approval and cost (D-11, D-13, D-14)",
        "",
        "Rafael's ruling, verbatim:",
        "",
        f"> {a['ruling']}",
        "",
        "His R-3 b conditions, verbatim:",
        "",
        f"> {a['r3_conditions']}",
        "",
        "His record-total sentence, verbatim:",
        "",
        f"> {a['record_total_ruling']}",
        "",
        *_table(
            ("quantity", "hours"),
            [
                [key, repr(a[key])]
                for key in (
                    "e2_projection_hours",
                    "committed_front_hours_e2",
                    "e2_stop_hours",
                    "committed_total_hours",
                    "e2_total_hours",
                    "e2_e5_e6_total_hours",
                    "e2_e5_e6_total_hours_e6_actual_gate",
                )
            ],
        ),
        f"Rulings: {', '.join(f'{k} {v}' for k, v in a['rulings'].items())}; D-11 approved "
        f"{a['d11_approved']}; D-13 included {a['d13_included']} ({a['d13_nlls_per_adapter']} "
        f"NLLs per adapter, {a['d13_adapters']} adapters).",
        "",
    ]

    out += [
        "## Seeds (D-15)",
        "",
        *_table(
            ("seed", "outcome"),
            [[s, seeds["outcomes"][s]] for s in _seed_order(seeds["outcomes"])],
        ),
    ]
    for s in _seed_order(seeds["dropped_attempts"]):
        launch = record["provenance"]["seeds"][s].get("git_sha_at_launch")
        for attempt in seeds["dropped_attempts"][s]:
            out += [f"Seed {s} was re-run after a dropped attempt:", ""]
            out += _attempt_lines(attempt, launch)
            out += [
                *(
                    f"- {g} adapter, this attempt vs the dropped one: "
                    f"{_identity_text(attempt['adapter_identity'][g])}"
                    for g in groups
                ),
                "",
            ]
    for s in _seed_order(seeds["dropped_seed_outputs"]):
        left = seeds["dropped_seed_outputs"][s]
        out += [f"Seed {s} is left dropped (no relaunch re-ran it):", ""]
        for manifest in left["manifests"]:
            out += _attempt_lines(manifest, None)
        out += _table(
            ("partial output in place", "sha256"),
            [[i["from"], i["sha256"]] for i in left["in_place"]],
        )
    if not seeds["dropped_attempts"] and not seeds["dropped_seed_outputs"]:
        out += ["no dropped attempt", ""]

    label = record["a2_label"]
    rows, tiers = [], []
    for s in _seed_order(per_seed):
        for g in groups:
            slots = per_seed[s][g]["slots"]
            for slot in _slot_order(slots):
                r = slots[slot]
                tiers = sorted(r["per_tier"])
                rows.append(
                    [
                        s,
                        g,
                        slot,
                        r["fact_id"],
                        f"{r['n_answerable']}/{r['n_questions']}",
                        repr(r["rate"]),
                        *(
                            f"{r['per_tier'][t]['n_answerable']}/{r['per_tier'][t]['n_questions']}"
                            for t in tiers
                        ),
                    ]
                )
    out += [
        "## A2 recall per seed with its denominator (NOISE-01)",
        "",
        f"Every A2 record of both groups carries config.arm {label['label']!r} because it names "
        f"the pinned A2 pass, not a group: {label['explanation']}",
        "",
        *_table(("seed", "group", "slot", "fact", "recall", "rate", *tiers), rows),
    ]

    crn = record["crn_addendum"]
    out += ["## Training-seed floor beside v3.0's sampling floor (NOISE-02, D-01..D-05)", ""]
    if measured:
        rf = record["recall_floor"]
        pub, beside = rf["published"], rf["beside"]
        out += [
            *(
                f"- {g} group floor {rf[g]['floor']!r} (max {rf[g]['max']!r}, min "
                f"{rf[g]['min']!r}): {rf[g]['n_seeds']} whole seeds, {rf[g]['n_pairs']} pairs "
                "entered"
                for g in groups
            ),
            "",
            f"Published floor: {pub['value']!r} (group {pub['group']}, tie {pub['tie']}): "
            f"{pub['n_seeds']} whole seeds, {pub['n_pairs']} pairs entered; beside v3.0's "
            f"sampling floor {beside['sampling_floor']!r}; the (b) margin at the gate "
            f"{beside['margin_at_gate']!r}, not amended (margin_amended "
            f"{beside['margin_amended']}).",
            "",
        ]
    else:
        out += ["No floor is published: the record status is INSUFFICIENT_SEEDS.", ""]
    out += [
        "Rafael's confirmation g, verbatim:",
        "",
        f"> {crn['confirmation_g']}",
        "",
        "Every adapter is drawn at the same generator states (common random numbers), while "
        f"v3.0's sampling floor {crn['v3_sampling_floor']!r} ({crn['source']}) used independent "
        "draws: under common random numbers the training-seed floor is not an upper bound on "
        "training plus sampling and may come out below that value.",
        "",
    ]
    if crn.get("published_below_v3_sampling_floor"):
        out += [
            f"The published floor {record['recall_floor']['published']['value']!r} is below "
            f"v3.0's sampling floor {crn['v3_sampling_floor']!r}, as the addendum allows.",
            "",
        ]

    out += ["## Every pair (D-02, D-04)", ""]
    out += (
        _table(
            ("group", "seeds", "d", "deltas"),
            [
                [g, _seeds_text(p["seeds"]), repr(p["d"]), ", ".join(map(repr, p["deltas"]))]
                for g in groups
                for p in record["recall_floor"][g]["pairs"]
            ],
        )
        if measured
        else ["not published (INSUFFICIENT_SEEDS)", ""]
    )
    out += ["## Per-slot spread (D-04)", ""]
    out += (
        _table(
            ("group", "slot", "rates", "counts", "range", "sd_sample", "sd_population"),
            [
                [
                    g,
                    slot,
                    ", ".join(map(repr, sp["rates"])),
                    ", ".join(f"{n}/{q}" for n, q in sp["counts"]),
                    repr(sp["range"]),
                    repr(sp["sd_sample"]),
                    repr(sp["sd_population"]),
                ]
                for g in groups
                for per_slot in (record["recall_floor"][g]["per_slot"],)
                for slot in _slot_order(per_slot)
                for sp in (per_slot[slot],)
            ],
        )
        if measured
        else ["not published (INSUFFICIENT_SEEDS)", ""]
    )

    out += ["## gap_noise_floor (D-09, D-10)", ""]
    if measured:
        d, m2 = record["gap_noise_floor_detail"], record["m2_gap_descriptive"]
        out += [
            f"gap_noise_floor = {record['gap_noise_floor']!r} (max {d['max']!r}): {d['n_seeds']} "
            f"whole seeds, {d['n_pairs']} pairs entered; beside the v3.0/v4.0 one-pair floor "
            f"{d['beside']!r}.",
            "",
            *_table(
                ("seeds", "abs gap difference"),
                [[_seeds_text(p["seeds"]), repr(p["abs_gap_difference"])] for p in d["pairs"]],
            ),
            f"M2 group, descriptive, never a verdict: {m2['value']!r} (max {m2['max']!r}): "
            f"{m2['n_seeds']} whole seeds, {m2['n_pairs']} pairs entered.",
            "",
        ]
    else:
        out += ["No gap_noise_floor is published: not published (INSUFFICIENT_SEEDS).", ""]
    out += _table(
        (
            "seed",
            "group",
            "device",
            "adapter_on",
            "adapter_off",
            "committed adapter_off",
            "matches",
            "pre adapter_on",
            "pre adapter_off",
            "pre matches",
            "rehearsal",
            "pre_post_equal",
            "gap",
        ),
        [
            [
                s,
                g,
                r["device"],
                repr(r["adapter_on"]),
                repr(r["adapter_off"]),
                repr(r["committed_adapter_off"]),
                r["adapter_off_matches_committed"],
                repr(r["pre"]["adapter_on"]),
                repr(r["pre"]["adapter_off"]),
                r["pre"]["adapter_off_matches_committed"],
                r["rehearsal"],
                r["pre_post_equal"],
                repr(r["gap"]),
            ]
            for s in _seed_order(per_seed)
            for g in groups
            for r in (per_seed[s][g]["dialogue_gap"],)
        ],
    )

    out += ["## Full x M2 re-reading (D-12, descriptive)", "", "descriptive, never a verdict.", ""]
    out += (
        _table(
            ("slot", "v3.0 delta_taught_to_m2", "full seed", "M2 seed", "same seed", "m2 - full"),
            [
                [
                    slot,
                    repr(block["v3_delta_taught_to_m2"]),
                    p["full_seed"],
                    p["m2_seed"],
                    p["same_seed"],
                    repr(p["m2_minus_full"]),
                ]
                for slot in _slot_order(record["d12"]["per_slot"])
                for block in (record["d12"]["per_slot"][slot],)
                for p in block["pairs"]
            ],
        )
        if measured
        else ["not computed (INSUFFICIENT_SEEDS)", ""]
    )

    d07 = record["d07"]["m2_seed1337"]
    out += [
        "## Determinism check (D-07, descriptive)",
        "",
        "descriptive, never a verdict: every comparison is tensor by tensor, never the file "
        "sha256.",
        "",
        *_table(
            ("new adapter vs committed", "reading"),
            [[key, _identity_text(value)] for key, value in record["identity"].items()],
        ),
    ]
    if isinstance(d07, str):
        out += [f"M2@1337 A2 counts vs results/phase19_arm_retrain.json: {d07}", ""]
    else:
        out += [
            "M2@1337 A2 counts vs results/phase19_arm_retrain.json, label: "
            f"{d07['label'] or 'none (tensor-identical)'}",
            "",
            *_counts_table(d07["counts"]),
            _draws_text(d07["draw_identity"]),
            "",
        ]

    d08, d08b = record["d08"], record["d08b"]
    out += [
        "## persona_adapter.pt correction and the Phase 18 residual (D-08, D-08b)",
        "",
        d08["statement"],
        "",
        "persona_adapter.pt vs the dialogue-floor seed-1337 adapter, re-measured: "
        f"{_identity_text(d08['persona_vs_dialogue_floor_1337'])}",
        "",
    ]
    if isinstance(d08b, str):
        out += [f"D-08b: {d08b}", ""]
    else:
        out += [
            f"D-08b outcome {d08b['outcome']}, max abs rate difference "
            f"{d08b['max_abs_rate_difference']!r} (full@1337 vs the Phase 18 run_arm counts):",
            "",
            *_counts_table(d08b["counts"]),
            _draws_text(d08b["draw_identity"]),
            "",
        ]

    out += ["## Target rank across the M2 seeds (D-13, descriptive)", ""]
    if record["d13"] is None:
        out += ["D-13 was not approved: not measured.", ""]
    else:
        reading, blocks = record["d13"]["reading"], record["d13"]["blocks"]
        out += [
            "descriptive, never a verdict. Measured seeds: "
            f"{_seeds_text(reading['measured_seeds'])}.",
            "",
            *(
                f"- seed {nm['seed']}: not measured ({nm['failure_kind']}): {nm['reason']} — the "
                "seed is kept: ruling c"
                for nm in reading["not_measured"]
            ),
            "",
            *_table(
                (
                    "seed",
                    "anchor gate rank",
                    "A2 exposure rank",
                    "R_q committed n1/n",
                    "R_q minted n1/n",
                ),
                [
                    [
                        s,
                        b["anchor_gate"]["rank"],
                        b["anchor_gate"]["a2_record_rank"],
                        f"{b['r_q']['committed']['n1']}/{b['r_q']['committed']['n']}",
                        f"{b['r_q']['minted']['n1']}/{b['r_q']['minted']['n']}",
                    ]
                    for s in _seed_order(blocks)
                    for b in (blocks[s],)
                    if b["measured"]
                ],
            ),
        ]

    out += [
        "## Predictions recorded before the run",
        "",
        *_table(
            ("prediction", "as written", "observed", "criterion"),
            [
                [
                    key,
                    p["prediction"],
                    p["observed"]
                    if isinstance(p["observed"], str)
                    else json.dumps(p["observed"], sort_keys=True),
                    p["criterion"],
                ]
                for key in _prereg().ENTRIES["predictions"]["value"]
                for p in (record["predictions"][key],)
            ],
        ),
    ]

    emit_block = record["provenance"]["emit"]
    out += ["## Provenance", ""]
    for s in _seed_order(record["provenance"]["seeds"]):
        run = record["provenance"]["seeds"][s]
        out += [f"- seed {s} run: " + ", ".join(f"{k} {run[k]}" for k in sorted(run)), ""]
        out += _disclosure_lines(s, record["rehearsal_disclosure"][s])
    out += [
        f"- emit: device {emit_block['device']}, head at write `{emit_block['head_at_write']}`, "
        f"written {emit_block['written_utc']}",
        "- modules changed since launch: "
        f"{', '.join(emit_block['modules_changed_since_launch']) or 'none'}",
        "",
    ]
    return "\n".join(out)


def _tracked_and_clean(rel):
    """True iff ``rel`` is tracked and unmodified against HEAD (cwd _REPO)."""
    return all(
        subprocess.run(("git", *args), cwd=_REPO, capture_output=True).returncode == 0
        for args in (("ls-files", "--error-unmatch", rel), ("diff", "--quiet", "HEAD", "--", rel))
    )


def report(*, root=None):
    """Write results/phase40_noise_floor_report.md ONCE from the record (on the real root only
    from a tracked, unmodified record)."""
    root = pathlib.Path(root) if root is not None else pathlib.Path(_ROOT)
    prereg = _prereg()
    record_path = root / prereg.NOISE_FLOOR_RECORD
    _prove(record_path.exists(), f"{record_path} is missing: emit the record first")
    _prove(
        not _is_real(root) or _tracked_and_clean(prereg.NOISE_FLOOR_RECORD),
        f"{prereg.NOISE_FLOOR_RECORD} must be committed and unmodified before the report renders "
        "it",
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
