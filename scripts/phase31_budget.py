"""PHASE 31 ARCAL-03 — the v5.0 sweep + relearning budget and the Phase 32 stop line (D-07..D-10).

A RESOURCE RECORD, NOT AN OUTCOME THRESHOLD. The budget prices wall-clock from the two committed
MPS cost probes (``results/phase31_probe_point.json``, ``results/phase31_probe_relearn.json``) and
the 12 committed Phase 25 ``adv`` point records, and pre-commits the stop line Phase 32 pauses at.
Nothing here reads or gates a verdict (ROADMAP pre-registration boundary).

:func:`derive` is pure arithmetic over records; :func:`build_record` reads only COMMITTED blobs
(``phase30_points._tracked_json``) and is a recompute valid at any later commit; :func:`emit` is
write-once and refuses once any Phase 32 sweep point is tracked.

Torch-free at import AND at derive: replay windows come from the committed calibration's recipe,
steps from ``mitigation_budget.STEP_BUDGET`` (never the torch-importing helpers).
"""

import datetime
import hashlib
import itertools
import pathlib
import statistics
import sys

_GIT_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_GIT_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
_SRC = str(_GIT_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import mitigation_budget  # noqa: E402  (scripts/ is not a package)
import phase25_run  # noqa: E402  (same)
import phase29_prereg  # noqa: E402  (same)
import phase30_points  # noqa: E402  (same)
import phase31_probe  # noqa: E402  (same — torch-free at import)

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402

INSTRUMENT_GIT_SHA = git_sha()

# D-08: Phase 32 pauses when cumulative sweep wall-clock exceeds this x sweep.scheduled.high.
STOP_LINE_FACTOR = 1.5

BUDGET_RECORD = next(
    p for p in phase29_prereg.V5_RESULT_PATHS if p.startswith("results/phase31_budget")
)

PINNED_MODULES = tuple(
    pathlib.Path(path).resolve().relative_to(_GIT_ROOT).as_posix()
    for path in (
        __file__,
        phase31_probe.__file__,
        phase29_prereg.__file__,
        phase30_points.__file__,
        mitigation_budget.__file__,
    )
)

STAGES = ("train", "measure", "recall", "draw", "score")
RATIO_STAGES = ("measure", "recall", "draw")
BOUNDS = ("estimate", "low", "high")

RESOURCE_NOT_OUTCOME = (
    "This is a RESOURCE record plus a pre-committed stop line (D-08), not an outcome threshold: "
    "no verdict, floor or admission reads it (ROADMAP pre-registration boundary)."
)

FORMULA = {
    "n64": "per_point.n64[stage] = probe point record stages[stage].seconds (measured on MPS)",
    "per_window": (
        "per_window = (probe train - Phase 25 n64 ratio-0 twin train) / "
        "(STEP_BUDGET x replay_windows(n64)); must be > 0"
    ),
    "n8_train": (
        "Q1 lock: n8 train = Phase 25 n8 ratio-0 twin train + STEP_BUDGET x replay_windows(n8) x "
        "per_window (replay-window increment form)"
    ),
    "n8_ratios": (
        "Q1 lock: n8[stage] = n64[stage] x MEDIAN over the RATIO_GRID pairs of Phase 25 "
        "n8[stage]/n64[stage], matched by ratio, for measure, recall, draw (median: the robust "
        "central statistic, consistent with the project's median + min/max reporting)"
    ),
    "n8_score": "n8 score = n64 score: no Phase 25 figure exists for the score stage (stated)",
    "spread": (
        "D-10: spread[stage] = [min/median, max/median] of the 12 Phase 25 adv values of that "
        "stage; low/high = sum over stages of stage x factor"
    ),
    "score_spread": "score spread = [1, 1]: no Phase 25 figure to spread it by (stated)",
    "branches": (
        "D-12 per leg: learnable = len(leg_keys(leg)) x per_point; unlearnable = the control "
        "only (REFUSED records cost ~0 s); sweep.scheduled = the all-learnable branch"
    ),
    "stop_line": "D-08: stop_line.seconds = STOP_LINE_FACTOR x sweep.scheduled.high",
    "relearning": (
        "D-07: scheduled 0 (Phase 29 D-15 option 2). Conditional per leg, for a in "
        "1..len(leg_keys(leg))-1 admitted points: (len(FRESH_SEEDS) + 1 control + a mitigated) x "
        "arm + a x full_k_rescore.per_point. arm = relearn arm_seconds; its low/high scale train "
        "by the train spread, rung draws by the draw spread, rung remainders by the recall spread"
    ),
    "full_k_rescore": (
        "Q2 lock: full_k_rescore.per_point = max over the probe's rungs of "
        "(draw_seconds x FULL_K / k + remainder_seconds); k = the relearn record's draws per "
        "question (== CURVE_K on the committed record)"
    ),
    "q3": "Q3 lock: consumes the relearn record's per-rung draw/remainder split",
    "q4": "Q4 lock: emit order point -> relearn -> budget, each in a separate commit",
}


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase31_budget] {message}")


def _sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _hours(block):
    return {k: v / 3600 for k, v in block.items()}


def _range(estimate, low, high):
    block = {"estimate": estimate, "low": low, "high": high}
    return dict(block, hours=_hours(block))


def derive(*, point, relearn, table, recipe, max_steps):
    """The locked D-07..D-10 budget arithmetic. Pure: no I/O, no torch."""
    measured = point["leg"]
    _prove(measured in phase29_prereg.LEGS, f"probe leg {measured!r} is not one of the legs")
    rows = table["points"]
    _prove(list(rows) == list(phase29_prereg.POINT_KEYS()), "table does not cover POINT_KEYS()")

    # D-10 spread, per stage over the 12 Phase 25 adv values.
    spread = {}
    for stage in STAGES[:-1]:
        values = [r[stage] for r in rows.values()]
        med = statistics.median(values)
        spread[stage] = [min(values) / med, max(values) / med]
    spread["score"] = [1.0, 1.0]

    # n64 (the probed leg) straight from the probe; D-09 per-window replay increment.
    stages = {s: float(point["stages"][s]["seconds"]) for s in STAGES}
    twin = rows[phase29_prereg.control_key(measured)]["train"]
    per_window = (stages["train"] - twin) / (max_steps * recipe[measured]["replay_windows"])
    _prove(
        per_window > 0,
        f"per_window {per_window!r} <= 0: the probe's train {stages['train']}s does not exceed "
        f"the Phase 25 no-replay twin's {twin}s",
    )
    (other,) = [leg for leg in phase29_prereg.LEGS if leg != measured]  # the derived (unprobed) leg
    pairs_by_key = list(zip(phase29_prereg.leg_keys(other), phase29_prereg.leg_keys(measured)))
    ratios = {}
    for stage in RATIO_STAGES:
        pairs = [rows[a][stage] / rows[b][stage] for a, b in pairs_by_key]
        ratios[stage] = {"pairs": pairs, "median": statistics.median(pairs)}
    per_point = {
        measured: stages,
        other: {
            "train": rows[phase29_prereg.control_key(other)]["train"]
            + max_steps * recipe[other]["replay_windows"] * per_window,
            **{s: stages[s] * ratios[s]["median"] for s in RATIO_STAGES},
            "score": stages["score"],
        },
    }
    for leg, p in per_point.items():
        total = sum(p[s] for s in STAGES)
        low = sum(p[s] * spread[s][0] for s in STAGES)
        high = sum(p[s] * spread[s][1] for s in STAGES)
        p.update(
            total=total,
            low=low,
            high=high,
            hours=_hours({"total": total, "low": low, "high": high}),
        )
    per_point = {leg: per_point[leg] for leg in phase29_prereg.LEGS}

    # D-12 branches.
    per_leg = {}
    for leg, p in per_point.items():
        n = len(phase29_prereg.leg_keys(leg))
        per_leg[leg] = {
            "points": n,
            "learnable": _range(n * p["total"], n * p["low"], n * p["high"]),
            "unlearnable": _range(p["total"], p["low"], p["high"]),
        }
    branches = []
    for combo in itertools.product(("learnable", "unlearnable"), repeat=len(phase29_prereg.LEGS)):
        legs = dict(zip(phase29_prereg.LEGS, combo))
        sums = {b: sum(per_leg[leg][legs[leg]][b] for leg in legs) for b in BOUNDS}
        branches.append({"legs": legs, **_range(*(sums[b] for b in BOUNDS))})
    scheduled = next(b for b in branches if set(b["legs"].values()) == {"learnable"})

    # D-07 relearning: priced, never scheduled.
    train = float(relearn["stages"]["train"]["seconds"])
    rungs = relearn["stages"]["rungs"]
    scale = phase29_prereg.FULL_K / relearn["k"]

    def _arm(i):
        return train * spread["train"][i] + sum(
            r["draw_seconds"] * spread["draw"][i] + r["remainder_seconds"] * spread["recall"][i]
            for r in rungs
        )

    def _rescore(i):
        return max(
            r["draw_seconds"] * scale * spread["draw"][i]
            + r["remainder_seconds"] * spread["recall"][i]
            for r in rungs
        )

    arm = _range(float(relearn["arm_seconds"]), _arm(0), _arm(1))
    rescore = _range(
        max(r["draw_seconds"] * scale + r["remainder_seconds"] for r in rungs),
        _rescore(0),
        _rescore(1),
    )
    _prove(rescore["estimate"] > 0, "the FULL_K re-score estimate is not > 0")
    arms = len(phase29_prereg.FRESH_SEEDS) + 1
    conditional = {
        leg: {
            str(a): _range(*((arms + a) * arm[b] + a * rescore[b] for b in BOUNDS))
            for a in range(1, len(phase29_prereg.leg_keys(leg)))
        }
        for leg in phase29_prereg.LEGS
    }

    stop_seconds = STOP_LINE_FACTOR * scheduled["high"]
    table_rows = list(rows.values())
    no_recall = sum(r["train"] + r["measure"] + r["draw"] for r in table_rows)
    with_recall = no_recall + sum(r["recall"] for r in table_rows)
    return {
        "requirement": "ARCAL-03",
        "resource_not_outcome": True,
        "resource_not_outcome_reason": RESOURCE_NOT_OUTCOME,
        "formula": FORMULA,
        "inputs": {
            "point": {s: stages[s] for s in STAGES},
            "point_leg": measured,
            "relearn": {
                "train_seconds": train,
                "rungs": rungs,
                "arm_seconds": relearn["arm_seconds"],
                "k": relearn["k"],
            },
            "table": rows,
            "replay_windows": {leg: recipe[leg]["replay_windows"] for leg in phase29_prereg.LEGS},
            "max_steps": max_steps,
            "full_k": phase29_prereg.FULL_K,
            "fresh_seeds": len(phase29_prereg.FRESH_SEEDS),
        },
        "derived": {
            "per_window_seconds": per_window,
            "derived_leg": other,
            "ratios": ratios,
        },
        "spread": spread,
        "per_point": per_point,
        "sweep": {"per_leg": per_leg, "branches": branches, "scheduled": scheduled},
        "relearning": {
            "scheduled_seconds": 0,
            "scheduled_reason": (
                "Phase 29 D-15 option 2: no GATE-08 promotion is pre-registered, so no relearning "
                "leg is scheduled; the full conditional cost is recorded below"
            ),
            "arm_seconds": arm,
            "full_k_rescore": {
                "per_point_seconds": rescore,
                "basis": (
                    "phase27_relearn.run_gate: promote_at_z may promote an admitted point, then "
                    "score_rung re-scores it at FULL_K (scripts/phase27_relearn.py:999-1011)"
                ),
                "reason": (
                    "An upper bound: every admitted point promoted, priced at the costliest rung. "
                    "Draws scale linearly in k (k - 1 samples + the greedy draw); the remainder "
                    "(recall + corpus build + scoring) does not. D-15 option 2 governs GATE-08 "
                    "sweep-point promotion, a different promotion, so it does not zero this line"
                ),
            },
            "conditional": conditional,
            "arm_unit_note": (
                "Every leg relearns with the same 8-fact attacker bin and the same scoring corpus, "
                "so one arm unit prices both legs"
            ),
        },
        "stop_line": {
            "factor": STOP_LINE_FACTOR,
            "basis": "STOP_LINE_FACTOR x sweep.scheduled.high (D-08, D-10)",
            "seconds": stop_seconds,
            "hours": stop_seconds / 3600,
            "consumer": (
                "Phase 32 reads results/phase31_budget.json::stop_line.seconds; never retype it"
            ),
        },
        "reconciliation": {
            "phase25_sum_hours": {"no_recall": no_recall / 3600, "with_recall": with_recall / 3600},
            "unsourced_estimate": "~25-30 h",
            "unsourced_estimate_origin": (
                ".planning/milestones/v4.0-phases/"
                "25-frontier-sweep-and-the-existence-gate-verdict/25-HUMAN-UAT.md:49"
            ),
            "note": (
                "The ~25-30 h estimate was never derived; the 12 committed Phase 25 adv points sum "
                "to phase25_sum_hours (computed here), with no replay term. This budget replaces it"
            ),
        },
        "notes": [
            "D-01: the n8 control is never probed; its cost is derived only by the D-09 formula.",
            "RESEARCH Pitfall 5: phase25_points.measure_stage scores recall only under "
            f"is_control, so the Phase 32 driver must add the recall producer for the "
            f"{len(phase29_prereg.POINT_KEYS()) - len(phase29_prereg.LEGS)} non-control points; "
            "this budget already prices recall at every trained point.",
        ],
    }


# =================================================================================================
# THE RECORD — committed blobs only — and the write-once emit (no --force)
# =================================================================================================


def require_no_sweep_point(tracked):
    """The budget precedes the sweep: refuse once any Phase 32 point record is tracked."""
    swept = [p for p in tracked if p.startswith(phase29_prereg.POINT_RECORD_PREFIX)]
    _prove(
        not swept,
        f"sweep point {swept[0] if swept else ''} is already tracked: the ARCAL-03 budget must "
        "precede every Phase 32 point, so it is never emitted after the sweep starts",
    )


def build_record(tracked):
    """A pure recompute from COMMITTED records, valid at any later commit (no sweep-point check)."""
    point = phase30_points._tracked_json(
        phase31_probe.POINT_RECORD, tracked, "the ARCAL-01 point probe"
    )
    relearn = phase30_points._tracked_json(
        phase31_probe.RELEARN_RECORD, tracked, "the ARCAL-02 relearn probe"
    )
    _prove(
        relearn["k"] == phase29_prereg.CURVE_K and relearn["rungs"] == list(phase29_prereg.RUNGS),
        f"the relearn record's k {relearn['k']} / rungs {relearn['rungs']} are not CURVE_K / RUNGS",
    )
    table = phase31_probe.phase25_stage_table(tracked)
    recipe = phase30_points.calibration_record(tracked)["recipe"]
    for leg in phase29_prereg.LEGS:
        _prove(
            recipe[leg]["max_steps"] == mitigation_budget.STEP_BUDGET,
            f"calibration recipe {leg} max_steps {recipe[leg]['max_steps']} != STEP_BUDGET",
        )
    record = derive(
        point=point,
        relearn=relearn,
        table=table,
        recipe=recipe,
        max_steps=mitigation_budget.STEP_BUDGET,
    )
    read = [
        phase31_probe.POINT_RECORD,
        phase31_probe.RELEARN_RECORD,
        *(row["source"] for row in table["points"].values()),
        table["recall_source"],
        phase30_points.CALIBRATION_PATH,
    ]
    # _tracked_json proved each working file == its HEAD blob, so these are the committed bytes.
    record["sources"] = {rel: _sha256(_GIT_ROOT / rel) for rel in read}
    return record


def emit(out_path=BUDGET_RECORD):
    """Write-once: overwrite refusal, dirty refusal, sweep-point refusal, then build and write."""
    out_path = pathlib.Path(out_path)
    if not out_path.is_absolute():
        out_path = _GIT_ROOT / out_path
    _prove(
        not out_path.exists(),
        f"{out_path} exists — REFUSING to overwrite it. The budget is write-once; corrections are "
        "dated continuations",
    )
    pathspec = ("scripts", "src", "results")
    if out_path.is_relative_to(_GIT_ROOT):
        pathspec += (f":(exclude){out_path.relative_to(_GIT_ROOT).as_posix()}",)
    refuse_if_dirty(
        who="phase31_budget",
        detail=(
            "the budget publishes git_sha and hashes its pinned modules from the working tree; a "
            "record written from a dirty tree names a commit it cannot be regenerated from"
        ),
        pathspec=pathspec,
        cwd=_GIT_ROOT,
    )
    tracked = phase31_probe._tracked()
    require_no_sweep_point(tracked)
    record = build_record(tracked)
    record["calibration"] = phase31_probe.calibration_descent()
    record["provenance"] = {
        "module_sha256": {rel: _sha256(_GIT_ROOT / rel) for rel in PINNED_MODULES},
        "git_sha": INSTRUMENT_GIT_SHA,
        "head_at_write": git_sha(),
        "written_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    phase25_run.atomic_write_json(out_path, record)
    print(
        f"[phase31_budget] stop line {record['stop_line']['hours']:.2f} h — wrote {out_path}",
        flush=True,
    )
    return record


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    _prove(not argv, f"usage: python scripts/phase31_budget.py (no arguments; got {argv})")
    emit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
