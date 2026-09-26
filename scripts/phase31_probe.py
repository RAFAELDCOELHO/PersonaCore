"""PHASE 31 ARCAL-01 / ARCAL-02 — the MPS cost probe: the point half (D-01..D-03, D-11), then the
relearning half (D-04..D-06), run in one unattended agent pass (D-12).

WHAT IT RUNS. The ``advr_n64`` CONTROL plan that ``phase30_points.next_action`` returns (so
``require_calibrated_recipe`` proves the committed recipe), re-keyed ONLY on ``point_key`` and
``prefix`` so no probe artifact can be reused by Phase 32 (D-02). The live stage sequence mirrors
``phase25_run.run_point`` without calling it: train -> measure (condition (c) + GATE-05, then the
control's taught recall, timed apart, D-03) -> the attack draws -> scoring.

WHAT IT PROVES. Replay ran: every replay draw is counted per optimizer step through ``train()``'s
``on_draw`` hook, and the count must equal the calibration's ``replay_windows`` on every step or
the run stops before measuring (D-11). The readings gate nothing; the record is a discarded,
isolated probe and never a sweep point.

THE RELEARNING HALF. ONE mitigated arm, seed ``DESIGNATED_SEED``, relearned to ``RELEARN_CAP``
from the point probe's own adapter through ``phase27_relearn.train_relearn_arm``, then scored at
every rung of ``RUNGS`` at ``CURVE_K`` through ``score_rung``, each rung timed. No admitted leg is
called.

Torch-free at import: ``teach_persona`` and every torch-touching module are imported lazily.
"""

import argparse
import datetime
import hashlib
import json
import pathlib
import shutil
import statistics
import subprocess
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent
# The git root. Same value as _ROOT at import, but never patched: every git call and every module
# hash reads it, so a test that redirects _ROOT (the data/ sidecars) changes no git answer.
_GIT_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_GIT_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
_SRC = str(_GIT_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import mitigation_budget  # noqa: E402  (scripts/ is not a package)
import phase25_points  # noqa: E402  (same)
import phase25_prereg  # noqa: E402  (same)
import phase25_record  # noqa: E402  (same)
import phase25_run  # noqa: E402  (same)
import phase27_prereg  # noqa: E402  (same)
import phase27_relearn  # noqa: E402  (same — torch-free at import)
import phase29_prereg  # noqa: E402  (same)
import phase30_points  # noqa: E402  (same)

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402

INSTRUMENT_GIT_SHA = git_sha()

# D-02 discretion lock: the probe's identity. Neither prefix resolves under phase3* or the v4.0
# calibration prefix, and the key is not a v5.0 point key (probe_plan proves all three).
PROBE_KEY = "probe31_advr_n64"
PROBE_PREFIX = "probe31"
RELEARN_LABEL = "probe31"
LEG = "n64"

POINT_RECORD = next(
    p for p in phase29_prereg.V5_RESULT_PATHS if p.startswith("results/phase31_probe_point")
)
RELEARN_RECORD = next(
    p for p in phase29_prereg.V5_RESULT_PATHS if p.startswith("results/phase31_probe_relearn")
)

PINNED_MODULES = tuple(
    pathlib.Path(path).resolve().relative_to(_GIT_ROOT).as_posix()
    for path in (
        __file__,
        phase25_points.__file__,
        phase25_run.__file__,
        phase30_points.__file__,
        phase27_relearn.__file__,
        _SCRIPTS + "/teach_persona.py",  # a path, not an import: teach_persona imports torch
        _SRC + "/personacore/training/loop.py",
    )
)

SWEEP_POINT_FALSE_REASON = (
    "This is the Phase 31 COST PROBE (ARCAL-01), not a sweep point. It re-keys the advr_n64 "
    f"control plan to {PROBE_KEY!r} / prefix {PROBE_PREFIX!r} (D-02) so none of its sidecars, "
    "adapter, checkpoint or draw cache can be reused by Phase 32; it is discarded after timing "
    "and is never a PREREG-01 point. Phase 32 retrains its own n64 control regardless."
)

READINGS_NOTE = (
    "Timing-only readings (D-01). The probe previews the n64 control recipe on the same code, but "
    "these readings gate nothing: no floor, control_gap or verdict reads them, and Phase 32 "
    "retrains and re-measures its own advr_n64 control regardless (RESEARCH Pitfall 4)."
)


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase31_probe] {message}")


def _sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _rel(path):
    path = pathlib.Path(path)
    return path.relative_to(_ROOT).as_posix() if path.is_relative_to(_ROOT) else str(path)


def point_replay_sidecar():
    return _ROOT / "data" / "probe31_point_replay.json"


def point_run_sidecar():
    return _ROOT / "data" / "probe31_point_run.json"


def _git(*args):
    return subprocess.run(
        ("git", *args), cwd=_GIT_ROOT, capture_output=True, text=True, check=True
    ).stdout


def _tracked():
    """``git ls-files results`` of the REAL repository — the ONLY tracked-list source."""
    return [line for line in _git("ls-files", "results").splitlines() if line]


# =================================================================================================
# IDENTITY (D-01, D-02) and REPLAY COUNTING (D-11)
# =================================================================================================


def probe_plan(tracked):
    """The advr_n64 control plan, re-keyed on point_key and prefix only."""
    control = phase29_prereg.control_key(LEG)
    action = phase30_points.next_action(control, tracked)
    _prove(action["action"] == "train", f"next_action({control!r}) is {action['action']!r}")
    plan = dict(action["plan"], point_key=PROBE_KEY, prefix=PROBE_PREFIX)
    _prove(plan["is_control"] and plan["arm"] == "advr_n64", f"plan is not the n64 control: {plan}")
    _prove(PROBE_KEY not in phase29_prereg.POINT_KEYS(), f"{PROBE_KEY!r} is a v5.0 point key")
    for label in (PROBE_PREFIX, RELEARN_LABEL):
        _prove(
            not label.startswith("phase3")
            and not label.startswith(phase25_points.CALIBRATION_PREFIX_LITERAL),
            f"probe label {label!r} resolves under a sweep or calibration prefix",
        )
    return plan


def per_step_replay(events):
    """Replay windows per optimizer step from ``(is_replay, n_windows)`` draws, in order.

    A teaching draw opens a step; replay draws land in the step they follow (``replay_fn`` runs
    after the step's teaching draw). ``tests/test_phase30_seam.py``'s bucketing, refusing loudly.
    """
    steps = []
    for is_replay, n_windows in events:
        if not is_replay:
            steps.append(0)
        else:
            _prove(steps, "a replay draw before any teaching draw")
            steps[-1] += n_windows
    return steps


def prove_replay_counts(events, expected, *, batch_size, steps):
    """D-11: exactly ``expected`` replay windows on EVERY step, not merely in total."""
    teaching = [n for is_replay, n in events if not is_replay]
    _prove(
        teaching == [batch_size] * steps,
        f"teaching draws {teaching[:5]}... ({len(teaching)}) are not {steps} x {batch_size}",
    )
    per_step = per_step_replay(events)
    _prove(
        per_step == [expected] * steps,
        f"replay windows per step {sorted(set(per_step))} are not {expected} on all {steps} steps "
        "(counted per step through on_draw)",
    )
    return per_step


# =================================================================================================
# THE PHASE 25 TWIN AND THE 12-POINT SPREAD (SC1) — committed records only, torch-free
# =================================================================================================


def phase25_stage_table(tracked):
    """Per-stage seconds of the 12 v4.0 ``adv`` twins of the v5.0 keys, from committed records."""
    recall_source = "results/phase25_recall.json"
    recall = phase30_points._tracked_json(recall_source, tracked, "the Phase 25 recall record")
    points = {}
    for leg in phase29_prereg.LEGS:
        for ratio in phase29_prereg.RATIO_GRID:
            v5 = phase29_prereg.point_key(f"advr_{leg}", ratio)
            v4 = phase25_record.point_key(f"adv_{leg}", ratio)
            source = phase25_prereg.point_record_path(v4)
            record = phase30_points._tracked_json(source, tracked, "the Phase 25 twin")
            points[v5] = {
                "v4_key": v4,
                "source": source,
                "train": record["training"]["seconds"],
                "measure": record["measure_seconds"],
                "draw": 60 * sum(s["minutes"] for s in record["shape_timing"].values()),
                "recall": recall["points"][v4]["scoring_seconds"],
            }
    _prove(
        list(points) == list(phase29_prereg.POINT_KEYS()),
        "the Phase 25 table does not cover exactly POINT_KEYS()",
    )
    return {"points": points, "recall_source": recall_source}


def _spread(values):
    return {
        "n": len(values),
        "min": min(values),
        "median": statistics.median(values),
        "max": max(values),
    }


def build_point_record(run, table):
    """The point record from the run sidecar and the Phase 25 table. Pure: no I/O, no torch."""
    reused, outer, measured = run["reused"], run["outer_seconds"], run["measured"]
    shape_seconds = 60 * sum(run["shape_minutes"].values())
    if not reused["draw"]:
        _prove(
            outer["draw"] >= shape_seconds,
            f"the draw stage's outer bracket {outer['draw']:.1f}s is shorter than its shapes' "
            f"{shape_seconds:.1f}s",
        )

    def _outer(stage):
        return None if reused[stage] else float(outer[stage])

    stages = {
        "train": {
            "seconds": float(run["training"]["seconds"]),
            "outer_seconds": _outer("train"),
            "resumed_from_step": run["training"]["resumed_from_step"],
            "reused": reused["train"],
        },
        # outer_seconds here brackets measure_stage whole, recall scoring included.
        "measure": {
            "seconds": float(measured["measure_seconds"]),
            "outer_seconds": _outer("measure"),
            "reused": reused["measure"],
        },
        "recall": {"seconds": float(measured["scoring_seconds"]), "reused": reused["measure"]},
        "draw": {
            "seconds": float(shape_seconds),
            "shape_minutes": dict(run["shape_minutes"]),
            "outer_seconds": _outer("draw"),
            "reused": reused["draw"],
            "draws_per_question": run["k"],
            "draws_per_question_source": "mitigation_budget.CURVE_K",
        },
        "score": {"seconds": float(run["score_seconds"]), "reused": False},
    }
    replay = run["replay"]
    _prove(
        replay["per_step"] == [replay["expected_per_step"]] * replay["steps"],
        f"the run sidecar's replay counts {sorted(set(replay['per_step']))} are not "
        f"{replay['expected_per_step']} on all {replay['steps']} steps",
    )
    readings = {
        k: v for k, v in measured.items() if k not in ("measure_seconds", "scoring_seconds")
    }
    rows = list(table["points"].values())
    minutes = [(r["train"] + r["measure"] + r["draw"]) / 60 for r in rows]
    per_point = _spread(minutes)
    per_point["with_recall"] = _spread([m + r["recall"] / 60 for m, r in zip(minutes, rows)])
    per_point["formula"] = "(training.seconds + measure_seconds + 60 * sum(shape minutes)) / 60"
    return {
        "schema": "phase31_probe_point/1",
        "requirement": "ARCAL-01",
        "sweep_point": False,
        "sweep_point_false_reason": SWEEP_POINT_FALSE_REASON,
        "probe_key": run["probe_key"],
        "probe_prefix": run["probe_prefix"],
        "control_key": run["control_key"],
        "leg": LEG,
        "arm": run["arm"],
        "recipe": run["recipe"],
        "device": run["device"],
        "torch_version": run["torch_version"],
        "stages": stages,
        "total_seconds": sum(s["seconds"] for s in stages.values()),
        "replay": {
            "per_step": replay["per_step"],
            "expected_per_step": replay["expected_per_step"],
            "steps": replay["steps"],
            "teaching_windows_per_step": replay["teaching_windows_per_step"],
            "all_steps_equal": True,  # proved above
        },
        "adapter": {
            "path": run["training"]["adapter"],
            "sha256": run["training"]["adapter_sha256"],
        },
        "readings": dict(readings, gates_nothing=True, note=READINGS_NOTE),
        "phase25_twin": table["points"][run["control_key"]],
        "phase25_per_point_minutes": per_point,
        "phase25_recall_source": table["recall_source"],
    }


# =================================================================================================
# THE LIVE RUN — phase25_run.run_point's stage sequence, re-keyed, without run_point itself
# =================================================================================================


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def run_point_probe(*, heartbeat_path=None):
    """Train -> measure -> draw -> score the re-keyed control; write the run sidecar. Returns it.

    Resumable per stage through the frozen stages' own sidecars and draw cache; a stage reused
    that way keeps its inner seconds and loses its outer bracket (flagged ``reused``).
    """
    import teach_persona as tp
    import torch

    heartbeat_path = (
        phase25_run.HEARTBEAT_PATH if heartbeat_path is None else pathlib.Path(heartbeat_path)
    )
    refuse_if_dirty(
        who="phase31_probe",
        detail=(
            "the probe records the commit it ran from; a run from a dirty tree times code that "
            "commit does not contain"
        ),
        pathspec=("scripts", "src", "results"),
        cwd=_GIT_ROOT,
    )
    phase25_run.disk_precheck()
    run_git_sha, device, torch_version = git_sha(), phase25_run.device(), torch.__version__
    started_utc = _now()

    sidecar = point_run_sidecar()
    if sidecar.exists():
        print(f"[phase31_probe] {_rel(sidecar)} exists: the point probe is complete", flush=True)
        return json.loads(sidecar.read_text(encoding="utf-8"))

    tracked = _tracked()
    plan = probe_plan(tracked)
    paths = tp.arm_outputs(plan["arm"], prefix=PROBE_PREFIX)
    train_sidecar = phase25_points.training_sidecar(PROBE_KEY)
    replay_sidecar = point_replay_sidecar()
    _prove(
        train_sidecar.exists() or not paths["checkpoint"].exists(),
        f"{_rel(paths['checkpoint'])} exists without {_rel(train_sidecar)}: a resume would time "
        "only the remaining steps and could not count the earlier steps' replay. Delete "
        f"{_rel(paths['checkpoint'])} and {_rel(paths['adapter'])} (if present) in a reviewed "
        "step, then rerun",
    )
    _prove(
        replay_sidecar.exists() or not train_sidecar.exists(),
        f"{_rel(train_sidecar)} exists without {_rel(replay_sidecar)}: the per-step replay counts "
        f"of that training cannot be recovered. Delete {_rel(train_sidecar)}, "
        f"{_rel(paths['adapter'])} and {_rel(paths['checkpoint'])} in a reviewed step, then rerun",
    )
    expected = phase30_points.calibration_record(tracked)["recipe"][LEG]["replay_windows"]
    n_facts = len(tp.arm_spec(plan["arm"])[0])
    _prove(
        expected == phase29_prereg.replay_windows(n_facts),
        f"the calibration's replay_windows {expected} != replay_windows({n_facts})",
    )
    reused = {
        "train": train_sidecar.exists(),
        "measure": phase25_points.measure_sidecar(PROBE_KEY).exists(),
        "draw": phase25_run.draws_path(PROBE_KEY).exists(),
    }

    state = {"point": PROBE_KEY, "stage": "train", "shape": None, "draw_index": None}
    outer = {}
    stop, thread = phase25_run.start_heartbeat(heartbeat_path, state)
    try:
        # TRAIN, with every draw counted through train()'s on_draw hook (D-11).
        events = []
        real_train = tp.train

        def _counting_train(**kwargs):
            def _on_draw(bin_path, ix):
                replay = pathlib.Path(bin_path) == pathlib.Path(tp.DIALOG_TRAIN_BIN)
                events.append((replay, len(ix)))

            return real_train(**kwargs, on_draw=_on_draw)

        tp.train = _counting_train
        started = time.monotonic()
        try:
            training = phase25_points.train_stage(plan)
        finally:
            tp.train = real_train
        outer["train"] = time.monotonic() - started
        if reused["train"]:
            _prove(not events, "a reused training drew windows")
            replay = json.loads(replay_sidecar.read_text(encoding="utf-8"))
            _prove(
                replay["adapter_sha256"] == training["adapter_sha256"],
                f"{_rel(replay_sidecar)} counts adapter {replay['adapter_sha256']!r}, not the "
                f"trained {training['adapter_sha256']!r}",
            )
        else:
            replay = {
                "per_step": prove_replay_counts(
                    events, expected, batch_size=tp.BATCH_SIZE, steps=tp.MAX_STEPS
                ),
                "expected_per_step": expected,
                "steps": tp.MAX_STEPS,
                "teaching_windows_per_step": tp.BATCH_SIZE,
                "adapter_sha256": training["adapter_sha256"],
            }
            phase25_run.atomic_write_json(replay_sidecar, replay)
        _prove(
            replay["per_step"] == [expected] * tp.MAX_STEPS,
            f"{_rel(replay_sidecar)} does not hold {expected} replay windows on all "
            f"{tp.MAX_STEPS} steps",
        )

        # MEASURE: condition (c) + GATE-05 (measure_seconds), then recall (scoring_seconds), D-03.
        state["stage"] = "measure"
        started = time.monotonic()
        measured = phase25_points.measure_stage(plan, training)
        outer["measure"] = time.monotonic() - started
        _prove(measured["scoring_seconds"] is not None, "the control's recall was not scored")

        state["stage"] = "draw"
        corpus, corpus_sha256 = phase25_points.attack_corpus()
        started = time.monotonic()
        blob, _digests = phase25_run.draw_point_shapes(
            PROBE_KEY,
            adapter=_ROOT / training["adapter"],
            adapter_sha256=training["adapter_sha256"],
            corpus=corpus,
            corpus_sha256=corpus_sha256,
            k=mitigation_budget.CURVE_K,
            state=state,
        )
        outer["draw"] = time.monotonic() - started
        state["shape"] = state["draw_index"] = None

        state["stage"] = "score"
        started = time.monotonic()
        phase25_run.score_point(blob, phase25_points.scoring_values())
        score_seconds = time.monotonic() - started
        outer["score"] = score_seconds

        state["stage"] = "record"
        run = {
            "probe_key": PROBE_KEY,
            "probe_prefix": PROBE_PREFIX,
            "control_key": phase29_prereg.control_key(LEG),
            "arm": plan["arm"],
            "recipe": phase30_points.calibration_record(tracked)["recipe"][LEG],
            "k": mitigation_budget.CURVE_K,
            "run_git_sha": run_git_sha,
            "device": device,
            "torch_version": torch_version,
            "started_utc": started_utc,
            "finished_utc": _now(),
            "reused": reused,
            "training": {
                "seconds": training["seconds"],
                "resumed_from_step": training["resumed_from_step"],
                "adapter": training["adapter"],
                "adapter_sha256": training["adapter_sha256"],
            },
            "outer_seconds": outer,
            "measured": measured,
            "shape_minutes": {f: s["timing"]["minutes"] for f, s in blob["shapes"].items()},
            "score_seconds": score_seconds,
            "replay": {k: v for k, v in replay.items() if k != "adapter_sha256"},
        }
        phase25_run.atomic_write_json(sidecar, run)
        # "done" BEFORE the stop event: a periodic beat racing the stop can only write "done".
        state.update(stage="done", shape=None, draw_index=None)
    finally:
        stop.set()
        thread.join()
    phase25_run.beat(heartbeat_path, point=PROBE_KEY, stage="done", shape=None, draw_index=None)
    print(f"[phase31_probe] point probe complete — wrote {_rel(sidecar)}", flush=True)
    return run


# =================================================================================================
# THE WRITE-ONCE EMIT (Phase 29 D-14: no retry, so no --force)
# =================================================================================================


def calibration_descent():
    """The add commit of the ARECIPE-02 calibration, derived, and proof HEAD descends from it."""
    path = phase30_points.CALIBRATION_PATH
    adds = _git("log", "--diff-filter=A", "--format=%H", "--", path).split()
    _prove(adds, f"{path} was never added in this history")
    add = adds[-1]
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", add, "HEAD"], cwd=_GIT_ROOT, capture_output=True
    )
    _prove(ancestor.returncode == 0, f"HEAD does not descend from {path}'s add commit {add}")
    return {"path": path, "add_commit": add, "is_ancestor_of_head": True}


def _emit_target(out_path):
    """Write-once: overwrite refusal FIRST, dirty-tree refusal SECOND. Returns the absolute path."""
    out_path = pathlib.Path(out_path)
    if not out_path.is_absolute():
        out_path = _GIT_ROOT / out_path
    _prove(
        not out_path.exists(),
        f"{out_path} exists — REFUSING to overwrite it. The probe record is write-once; "
        "corrections are dated continuations",
    )
    pathspec = ("scripts", "src", "results")
    if out_path.is_relative_to(_GIT_ROOT):
        pathspec += (f":(exclude){out_path.relative_to(_GIT_ROOT).as_posix()}",)
    refuse_if_dirty(
        who="phase31_probe",
        detail=(
            "the probe record publishes git_sha and hashes its pinned modules from the working "
            "tree; a record written from a dirty tree names a commit it cannot be regenerated from"
        ),
        pathspec=pathspec,
        cwd=_GIT_ROOT,
    )
    return out_path


def _write_record(out_path, record, run):
    """The calibration descent and provenance blocks every probe record carries, then the write."""
    record["calibration"] = calibration_descent()
    record["provenance"] = {
        "run": {
            "git_sha": run["run_git_sha"],
            "device": run["device"],
            "torch_version": run["torch_version"],
            "started_utc": run["started_utc"],
            "finished_utc": run["finished_utc"],
        },
        "module_sha256": {rel: _sha256(_GIT_ROOT / rel) for rel in PINNED_MODULES},
        "git_sha": INSTRUMENT_GIT_SHA,
        "head_at_write": git_sha(),
        "written_utc": _now(),
    }
    phase25_run.atomic_write_json(out_path, record)
    print(f"[phase31_probe] wrote {out_path}", flush=True)
    return record


def emit_point(out_path=POINT_RECORD):
    """Write-once: overwrite refusal FIRST, dirty-tree refusal SECOND, then read and write."""
    out_path = _emit_target(out_path)
    tracked = _tracked()
    sidecar = point_run_sidecar()
    _prove(sidecar.exists(), f"{_rel(sidecar)} does not exist: run the point probe first")
    run = json.loads(sidecar.read_text(encoding="utf-8"))
    return _write_record(out_path, build_point_record(run, phase25_stage_table(tracked)), run)


def emit_relearn(out_path=RELEARN_RECORD):
    """Write-once, and chained: the run started from the COMMITTED point record's adapter."""
    out_path = _emit_target(out_path)
    for sidecar in (relearn_train_sidecar(), relearn_run_sidecar()):
        _prove(sidecar.exists(), f"{_rel(sidecar)} does not exist: run the relearn probe first")
    run = json.loads(relearn_run_sidecar().read_text(encoding="utf-8"))
    record = build_relearn_record(run)
    tracked = _tracked()
    point = phase30_points._tracked_json(POINT_RECORD, tracked, "the ARCAL-01 point probe")
    _prove(
        run["start_sha256"] == point["adapter"]["sha256"],
        f"the relearning start_sha256 {run['start_sha256']!r} is not the committed "
        f"{POINT_RECORD} adapter.sha256 {point['adapter']['sha256']!r} (D-05)",
    )
    record["point_record"] = {"path": POINT_RECORD, "adapter_sha256": point["adapter"]["sha256"]}
    return _write_record(out_path, record, run)


# =================================================================================================
# THE RELEARNING HALF (ARCAL-02, D-04..D-06) — one mitigated arm on the full ladder
# =================================================================================================

RELEARN_SWEEP_POINT_FALSE_REASON = (
    "This is the Phase 31 relearning COST PROBE (ARCAL-02), not a sweep point. It relearns ONE "
    f"mitigated arm labelled {RELEARN_LABEL!r} from the point probe's own adapter (D-05); every "
    "artifact carries that label, so none can be reused by Phase 32's relearning curve."
)

RELEARN_UNIT = (
    "D-04: one relearning arm = train_relearn_arm to RELEARN_CAP at DESIGNATED_SEED (stages.train) "
    "plus score_rung at every one of the RUNGS at CURVE_K (stages.rungs, each a fresh bracket; "
    "draw_seconds = 60 x sum of the draw cache's shape minutes, remainder = recall + corpus "
    "build + scoring). arm_seconds = train + sum of rung seconds."
)

RELEARN_READINGS_NOTE = (
    "Timing-only readings (D-04). They gate nothing and are never a point on Phase 32's curve."
)


def relearn_train_sidecar():
    return _ROOT / "data" / "probe31_relearn_train.json"


def relearn_run_sidecar():
    return _ROOT / "data" / "probe31_relearn_run.json"


def relearn_out_dir():
    return _ROOT / "data" / "probe31_relearn"


def relearn_rung_label(steps):
    return f"{RELEARN_LABEL}_{LEG}_rung{steps:04d}_k{phase29_prereg.CURVE_K}"


def _relearn_outputs():
    """``train_relearn_arm``'s own names, composed exactly as it composes them (phase27_relearn)."""
    import teach_persona as tp  # LAZY — torch-touching

    label = f"mitigated_{RELEARN_LABEL}"
    name = f"{phase27_prereg.ATTACKER_ARM}_{LEG}_{label}_seed{phase29_prereg.DESIGNATED_SEED}"
    return tp.arm_outputs(name, prefix=phase27_prereg.ATTACKER_PREFIX)


def relearn_moves():
    """``(source, destination)`` for the four leftovers train_relearn_arm writes outside out_dir.

    Each matches a ``tests/test_phase27_relearn.py::_real_tree_strays`` glob, so each is moved
    under ``relearn_out_dir()`` once the train sidecar is written (D-02/SC4).
    """
    outputs, out_dir = _relearn_outputs(), relearn_out_dir()
    return [
        (outputs["csv"], out_dir / "run.csv"),
        *((outputs[key], out_dir / outputs[key].name) for key in ("bin", "mask", "checkpoint")),
    ]


def _finish_relearn_moves(bin_sha256):
    """Idempotent: move what is left, accept what is done, refuse both-or-neither. Then prove the
    moved bin is the one trained on."""
    for src, dst in relearn_moves():
        if src.exists() and not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))  # phase25_points' csv idiom
            if dst.name == "run.csv":
                try:
                    src.parent.rmdir()
                except OSError:
                    pass
        else:
            _prove(
                dst.exists() and not src.exists(),
                f"{_rel(src)} and {_rel(dst)} are both {'present' if src.exists() else 'absent'} "
                "— REFUSING to guess which is the trained artifact; resolve it in a reviewed step",
            )
    (bin_dst,) = [dst for _src, dst in relearn_moves() if dst.name.endswith("_train.bin")]
    _prove(
        _sha256(bin_dst) == bin_sha256,
        f"{_rel(bin_dst)} does not hash to the train sidecar's bin_sha256 {bin_sha256}",
    )


def _rung_timing(rung):
    """``draw_seconds`` from the shape minutes and the bracket remainder, proved > 0."""
    draw_seconds = 60 * sum(rung["shape_minutes"].values())
    remainder = rung["seconds"] - draw_seconds
    _prove(
        remainder > 0,
        f"rung {rung['steps']}: remainder {remainder:.3f}s <= 0 — the {rung['seconds']:.1f}s "
        f"bracket does not cover its {draw_seconds:.1f}s of draws",
    )
    return {
        "steps": rung["steps"],
        "label": rung["label"],
        "seconds": float(rung["seconds"]),
        "draw_seconds": float(draw_seconds),
        "shape_minutes": dict(rung["shape_minutes"]),
        "remainder_seconds": float(remainder),
    }


def build_relearn_record(run):
    """The relearn record from the complete run sidecar. Pure: no I/O, no torch."""
    _prove(run["complete"] is True, "the relearn run sidecar is not complete")
    _prove(
        [r["steps"] for r in run["rungs"]] == list(run["ladder"]),
        f"scored rungs {[r['steps'] for r in run['rungs']]} are not the ladder {run['ladder']}",
    )
    rungs = [_rung_timing(rung) for rung in run["rungs"]]
    train = float(run["train"]["seconds"])
    return {
        "schema": "phase31_probe_relearn/1",
        "requirement": "ARCAL-02",
        "sweep_point": False,
        "sweep_point_false_reason": RELEARN_SWEEP_POINT_FALSE_REASON,
        "unit": RELEARN_UNIT,
        "relearn_label": run["relearn_label"],
        "leg": run["leg"],
        "arm": run["arm"],
        "seed": run["seed"],
        "relearn_cap": run["relearn_cap"],
        "rungs": list(run["ladder"]),
        "k": run["k"],
        "start_adapter": run["start_adapter"],
        "start_sha256": run["start_sha256"],
        "device": run["device"],
        "torch_version": run["torch_version"],
        "stages": {"train": {"seconds": train}, "rungs": rungs},
        "arm_seconds": train + sum(r["seconds"] for r in rungs),
        "readings": {
            "rungs": [dict(r["reading"], steps=r["steps"]) for r in run["rungs"]],
            "gates_nothing": True,
            "note": RELEARN_READINGS_NOTE,
        },
    }


def run_relearn_probe(*, heartbeat_path=None):
    """Relearn from the point probe's adapter, score every rung; write the run sidecar. Returns it.

    Resumable: a complete training (train sidecar) is reused, and a COMPLETED rung is reused. A
    rung with a draw cache but not completed is refused: a resume would time only its remainder.
    """
    import phase14_factset as fs  # LAZY — read at call time (the wiring proof patches it)
    import torch

    heartbeat_path = (
        phase25_run.HEARTBEAT_PATH if heartbeat_path is None else pathlib.Path(heartbeat_path)
    )
    refuse_if_dirty(
        who="phase31_probe",
        detail=(
            "the probe records the commit it ran from; a run from a dirty tree times code that "
            "commit does not contain"
        ),
        pathspec=("scripts", "src", "results"),
        cwd=_GIT_ROOT,
    )
    point_sidecar = point_run_sidecar()
    _prove(
        point_sidecar.exists(),
        f"{_rel(point_sidecar)} does not exist: the relearning starts from the point probe's own "
        "adapter, so the point probe runs first (D-05)",
    )
    point = json.loads(point_sidecar.read_text(encoding="utf-8"))["training"]
    run_sidecar, train_sidecar = relearn_run_sidecar(), relearn_train_sidecar()
    progress = {"complete": False, "rungs": []}
    if run_sidecar.exists():
        progress = json.loads(run_sidecar.read_text(encoding="utf-8"))
        if progress["complete"]:
            print(f"[phase31_probe] {_rel(run_sidecar)} is complete", flush=True)
            return progress
    checkpoint = relearn_moves()[-1][0]
    leftovers = [p for p in (relearn_out_dir(), checkpoint) if p.exists()]
    _prove(
        train_sidecar.exists() or not leftovers,
        f"{', '.join(_rel(p) for p in leftovers)} exist(s) without {_rel(train_sidecar)}: a "
        "half-trained relearning would time only its remaining rungs. Delete them in a reviewed "
        "step, then rerun",
    )
    phase25_run.disk_precheck()
    run_git_sha, device, torch_version = git_sha(), phase25_run.device(), torch.__version__
    started_utc = progress.get("started_utc", _now())

    state = {"point": RELEARN_LABEL, "stage": "train", "shape": None, "draw_index": None}
    stop, thread = phase25_run.start_heartbeat(heartbeat_path, state)
    try:
        if not train_sidecar.exists():
            start = _ROOT / point["adapter"]
            started = time.monotonic()
            trained = phase27_relearn.train_relearn_arm(
                arm="mitigated",
                leg=LEG,
                seed=phase29_prereg.DESIGNATED_SEED,
                cfg=phase27_relearn.shared_train_config(),
                start_adapter=start,
                expected_sha256=point["adapter_sha256"],
                out_dir=relearn_out_dir(),
                device=device,
                point_key=RELEARN_LABEL,
            )
            seconds = time.monotonic() - started
            phase25_run.atomic_write_json(
                train_sidecar,
                {
                    "seconds": seconds,
                    "start_adapter": _rel(start),
                    "start_sha256": point["adapter_sha256"],
                    "bin_sha256": trained["bin_sha256"],
                    "run_git_sha": run_git_sha,
                    "rungs": [
                        {
                            "steps": r["steps"],
                            "adapter_path": _rel(phase27_relearn._ROOT / r["adapter_path"]),
                            "adapter_sha256": r["adapter_sha256"],
                        }
                        for r in trained["rungs"]
                    ],
                    "moves": [[_rel(src), _rel(dst)] for src, dst in relearn_moves()],
                },
            )
        training = json.loads(train_sidecar.read_text(encoding="utf-8"))
        _prove(
            training["start_sha256"] == point["adapter_sha256"],
            f"{_rel(train_sidecar)} started from {training['start_sha256']!r}, not the point "
            f"probe's adapter {point['adapter_sha256']!r} (D-05)",
        )
        _prove(
            [r["steps"] for r in training["rungs"]] == list(phase29_prereg.RUNGS),
            f"trained rungs {[r['steps'] for r in training['rungs']]} are not the full ladder "
            f"{phase29_prereg.RUNGS} (D-04)",
        )
        _finish_relearn_moves(training["bin_sha256"])

        done = {r["steps"]: r for r in progress["rungs"]}
        rungs = []
        state["stage"] = "draw"
        for trained_rung in training["rungs"]:
            steps, label = trained_rung["steps"], relearn_rung_label(trained_rung["steps"])
            if steps in done:
                _prove(
                    done[steps]["adapter_sha256"] == trained_rung["adapter_sha256"],
                    f"completed rung {steps} scored adapter {done[steps]['adapter_sha256']!r}, "
                    f"not the trained {trained_rung['adapter_sha256']!r}",
                )
                rungs.append(done[steps])
                continue
            cache = phase25_run.draws_path(label)
            _prove(
                not cache.exists(),
                f"{_rel(cache)} exists but rung {steps} is not in the completed-rung list: an "
                "interrupted rung whose reused shapes would leave the bracket timing only the "
                "remainder. Delete it in a reviewed step, then rerun (no mid-rung resume)",
            )
            adapter = _ROOT / trained_rung["adapter_path"]
            _prove(
                _sha256(adapter) == trained_rung["adapter_sha256"],
                f"{_rel(adapter)} does not hash to its trained sha256",
            )
            started = time.monotonic()
            reading = phase27_relearn.score_rung(
                point_label=label,
                adapter_path=adapter,
                k=phase29_prereg.CURVE_K,
                out_dir=relearn_out_dir(),
                device=device,
                facts=fs.LOCKED_FACTS,
                values=phase25_points.scoring_values(),
            )
            seconds = time.monotonic() - started
            blob = json.loads(cache.read_text(encoding="utf-8"))
            rung = {
                "steps": steps,
                "label": label,
                "adapter_path": trained_rung["adapter_path"],
                "adapter_sha256": trained_rung["adapter_sha256"],
                "seconds": seconds,
                "shape_minutes": {f: s["timing"]["minutes"] for f, s in blob["shapes"].items()},
                "reading": reading,
            }
            _rung_timing(rung)  # remainder > 0, proved at run time as well as at build time
            rungs.append(rung)
            phase25_run.atomic_write_json(
                run_sidecar, {"complete": False, "started_utc": started_utc, "rungs": rungs}
            )

        state["stage"] = "record"
        run = {
            "complete": True,
            "relearn_label": RELEARN_LABEL,
            "leg": LEG,
            "arm": "mitigated",
            "seed": phase29_prereg.DESIGNATED_SEED,
            "relearn_cap": phase29_prereg.RELEARN_CAP,
            "ladder": list(phase29_prereg.RUNGS),
            "k": phase29_prereg.CURVE_K,
            "start_adapter": training["start_adapter"],
            "start_sha256": training["start_sha256"],
            "train": {
                "seconds": training["seconds"],
                "bin_sha256": training["bin_sha256"],
                "run_git_sha": training["run_git_sha"],
            },
            "rungs": rungs,
            "run_git_sha": run_git_sha,
            "device": device,
            "torch_version": torch_version,
            "started_utc": started_utc,
            "finished_utc": _now(),
        }
        phase25_run.atomic_write_json(run_sidecar, run)
        # "done" BEFORE the stop event: a periodic beat racing the stop can only write "done".
        state.update(stage="done", shape=None, draw_index=None)
    finally:
        stop.set()
        thread.join()
    phase25_run.beat(heartbeat_path, point=RELEARN_LABEL, stage="done", shape=None, draw_index=None)
    print(f"[phase31_probe] relearn probe complete — wrote {_rel(run_sidecar)}", flush=True)
    return run


# =================================================================================================
# THE CLI (D-12): one agent run measures the point, then the relearning arm from its adapter
# =================================================================================================


def build_parser():
    parser = argparse.ArgumentParser(
        description="Phase 31 MPS cost probe: the point probe, then one relearning arm (D-12)."
    )
    sub = parser.add_subparsers(dest="mode", required=True)
    run = sub.add_parser("run", help="run the point probe, then the relearn probe (resumable)")
    run.add_argument("--heartbeat", default=str(phase25_run.HEARTBEAT_PATH))
    emit = sub.add_parser("emit", help="write one write-once probe record under results/")
    emit.add_argument("target", choices=("point", "relearn"))
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.mode == "emit":
        (emit_point if args.target == "point" else emit_relearn)()
        return 0
    import phase25_venue  # torch-free; the banner lets the launch identity be read off the log

    print(phase25_venue.launch_banner(), flush=True)
    heartbeat = pathlib.Path(args.heartbeat)
    run_point_probe(heartbeat_path=heartbeat)  # D-05: the relearning starts from its adapter
    run_relearn_probe(heartbeat_path=heartbeat)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
