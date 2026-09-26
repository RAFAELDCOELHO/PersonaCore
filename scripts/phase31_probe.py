"""PHASE 31 ARCAL-01 — the MPS cost probe, point half (D-01..D-03, D-11).

WHAT IT RUNS. The ``advr_n64`` CONTROL plan that ``phase30_points.next_action`` returns (so
``require_calibrated_recipe`` proves the committed recipe), re-keyed ONLY on ``point_key`` and
``prefix`` so no probe artifact can be reused by Phase 32 (D-02). The live stage sequence mirrors
``phase25_run.run_point`` without calling it: train -> measure (condition (c) + GATE-05, then the
control's taught recall, timed apart, D-03) -> the attack draws -> scoring.

WHAT IT PROVES. Replay ran: every replay draw is counted per optimizer step through ``train()``'s
``on_draw`` hook, and the count must equal the calibration's ``replay_windows`` on every step or
the run stops before measuring (D-11). The readings gate nothing; the record is a discarded,
isolated probe and never a sweep point.

Torch-free at import: ``teach_persona`` and every torch-touching module are imported lazily.
"""

import hashlib
import pathlib
import statistics
import subprocess
import sys

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

import phase25_points  # noqa: E402  (scripts/ is not a package)
import phase25_prereg  # noqa: E402  (same)
import phase25_record  # noqa: E402  (same)
import phase25_run  # noqa: E402  (same)
import phase29_prereg  # noqa: E402  (same)
import phase30_points  # noqa: E402  (same)

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402, F401  (Task 2)

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

PINNED_MODULES = tuple(
    pathlib.Path(path).resolve().relative_to(_GIT_ROOT).as_posix()
    for path in (
        __file__,
        phase25_points.__file__,
        phase25_run.__file__,
        phase30_points.__file__,
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
