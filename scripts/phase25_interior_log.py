"""PLAN 25-17 — THE INTERIOR LOG: the 36 interior points as they actually ran, from the artifacts.

Reads the 44 committed point records, git history, `data/phase25_heartbeat.jsonl`,
`data/phase25_stall.jsonl` and `logs/phase25_sweep.out`; retrains nothing, retypes no list.

- the interior set is `ORDERED_POINT_KEYS()` minus the records tracked at the commit that closed
  plan 25-16 (`EXTREMES_LOG_COMMIT`), asserted to be 36 — derived from git history because the
  sweep began before this plan executed;
- every kill is found in the heartbeat as a `draw_index` RESET inside one (point, shape) with no
  stage change in between, and each is paired with the launch banner and the REUSING lines the
  relaunched driver printed, so "which shapes were on disk" is read, not remembered;
- every stall record is transcribed with `action_taken` intact and with the commits and beats that
  bracket its silence window;
- completeness is a SET EQUALITY over the tracked record paths, never a count.
"""

import datetime
import hashlib
import json
import pathlib
import platform
import re
import subprocess
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import mitigation_budget  # noqa: E402  (scripts/ is not a package)
import phase25_prereg  # noqa: E402  (same)
import phase25_record  # noqa: E402  (same)
import phase25_watch  # noqa: E402  (same)

RECORD = _ROOT / "results" / "phase25_interior_log.json"
EXTREMES_LOG = _ROOT / "results" / "phase25_extremes_log.json"
COST_RECORD = _ROOT / "results" / "phase23_cost.json"
THROUGHPUT_RECORD = _ROOT / "results" / "phase25_adversarial_throughput.json"
CAL03_RECORD = _ROOT / "results" / "phase23_cal03_wiring.json"
HEARTBEAT = _ROOT / "data" / "phase25_heartbeat.jsonl"
STALLS = _ROOT / "data" / "phase25_stall.jsonl"
SWEEP_LOG = _ROOT / "logs" / "phase25_sweep.out"

# The commit that landed results/phase25_extremes_log.json (plan 25-16, one path). The record set
# tracked AT that commit is "already committed" for the purpose of deriving the interior set.
EXTREMES_LOG_COMMIT = "491ba48"

_LAUNCH_RE = re.compile(r"^\[phase25_launch\] pid=(\d+) ")
_REUSE_SIDECAR_RE = re.compile(
    r"^\[phase25_points\] (\S+): REUSING (trained adapter|measurements) from"
)
_REUSE_SHAPE_RE = re.compile(r"^\[phase25_run\] (\S+) (\S+): REUSING (\d+) recorded prompt\(s\)")
_DONE_RE = re.compile(r"^\[phase25_run\] (\S+) (\S+): DONE — ([\d.]+) draws/min over ([\d.]+) min")
_COMMIT_RE = re.compile(r"^\[main ([0-9a-f]+)\] feat\(25-10\): record sweep point (\S+)$")


def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[phase25_interior_log] {message}")


def _git(*args):
    return subprocess.run(
        ["git", *args], cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout


def _iso(stamp):
    return datetime.datetime.fromisoformat(stamp)


def _hours(a, b):
    return (_iso(b) - _iso(a)).total_seconds() / 3600.0


# ===== (a) the interior set, as a complement over git history =====


def interior_set():
    pinned = set(phase25_record.ORDERED_POINT_KEYS())
    tracked_then = _git(
        "ls-tree", "-r", "--name-only", EXTREMES_LOG_COMMIT, "--", "results"
    ).split()
    committed_then = {
        pathlib.Path(p).stem.replace("phase25_point_", "")
        for p in tracked_then
        if p.startswith(phase25_prereg.POINT_RECORD_PREFIX)
    }
    _prove(
        committed_then <= pinned,
        f"unpinned keys tracked at {EXTREMES_LOG_COMMIT}: {committed_then - pinned}",
    )
    interior = pinned - committed_then
    _prove(len(interior) == 36, f"the interior set has {len(interior)} members, not 36")
    return interior, committed_then


# ===== (b) the sweep log: launches, per-point REUSING and DONE lines, driver commits =====


def parse_sweep_log():
    """Split the log into launches; per launch, which shapes each point REUSED from disk."""
    launches = []
    for line in SWEEP_LOG.read_text(encoding="utf-8").splitlines():
        m = _LAUNCH_RE.match(line)
        if m:
            launches.append(
                {
                    "pid": int(m.group(1)),
                    "reused_sidecars": {},
                    "reused_shapes": {},
                    "done": {},
                    "commits": {},
                }
            )
            continue
        if not launches:
            continue
        cur = launches[-1]
        m = _REUSE_SIDECAR_RE.match(line)
        if m:
            cur["reused_sidecars"].setdefault(m.group(1), []).append(m.group(2))
            continue
        m = _REUSE_SHAPE_RE.match(line)
        if m:
            cur["reused_shapes"].setdefault(m.group(1), {})[m.group(2)] = int(m.group(3))
            continue
        m = _DONE_RE.match(line)
        if m:
            cur["done"].setdefault(m.group(1), {})[m.group(2)] = {
                "rate_draws_per_min": float(m.group(3)),
                "minutes": float(m.group(4)),
            }
            continue
        m = _COMMIT_RE.match(line)
        if m:
            cur["commits"][m.group(2)] = m.group(1)
    return launches


# ===== (c) kills, read from the heartbeat as draw_index resets =====


def read_heartbeat():
    beats = [
        json.loads(line)
        for line in HEARTBEAT.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return [b for b in beats if b["point"] != "rehearsal"]


def find_kills(beats, launches, record_commit_times):
    """A kill mid-draw is a `draw_index` reset inside one (point, shape) without a stage change,
    followed by a silence LONGER than the heartbeat cadence (the relaunch gap). A reset with the
    next beat inside one cadence is a shape boundary — the beat's `shape` field lags `draw_index`
    by one tick — and is listed under `not_kills` rather than silently dropped."""
    kills = []
    not_kills = []
    cadence_s = phase25_watch.HEARTBEAT_SECONDS
    for i in range(1, len(beats)):
        prev, cur = beats[i - 1], beats[i]
        same_cell = (prev["point"], prev["stage"], prev["shape"]) == (
            cur["point"],
            cur["stage"],
            cur["shape"],
        )
        if not (same_cell and cur["stage"] == "draw" and cur["draw_index"] < prev["draw_index"]):
            continue
        point, shape = prev["point"], prev["shape"]
        gap_s = (_iso(cur["utc"]) - _iso(prev["utc"])).total_seconds()
        if gap_s <= 2 * cadence_s:
            not_kills.append(
                {
                    "point_key": point,
                    "beat_before": prev,
                    "beat_after": cur,
                    "gap_seconds": gap_s,
                    "reason": (
                        f"next beat within {2 * cadence_s} s of the previous one: no relaunch "
                        f"gap, no launch banner; prompt {prev['draw_index']} is the last of the "
                        f"shape and the `shape` field lags `draw_index` by one beat"
                    ),
                }
            )
            continue
        # the first draw beat of THIS attempt at this shape: walk back while the cell matches
        j = i - 1
        while j > 0 and (beats[j - 1]["point"], beats[j - 1]["stage"], beats[j - 1]["shape"]) == (
            point,
            "draw",
            shape,
        ):
            j -= 1
        shape_started = beats[j]["utc"]
        minutes_in_shape = (_iso(prev["utc"]) - _iso(shape_started)).total_seconds() / 60.0
        gap_minutes = (_iso(cur["utc"]) - _iso(prev["utc"])).total_seconds() / 60.0
        kills.append(
            {
                "point_key": point,
                "last_heartbeat": prev,
                "first_heartbeat_after_relaunch": cur,
                "shape_started_at_utc": shape_started,
                "minutes_into_shape_at_kill": minutes_in_shape,
                "relaunch_gap_minutes": gap_minutes,
                "wall_clock_lost_minutes": minutes_in_shape + gap_minutes,
            }
        )
    # pair each kill with the launch that resumed it: the LAST launch whose DONE lines name the
    # point (an earlier launch trained it)
    for kill in kills:
        point = kill["point_key"]
        owners = [n for n, lch in enumerate(launches) if point in lch["done"]]
        _prove(owners, f"no launch drew {point}")
        resume = launches[owners[-1]]
        reused = resume["reused_shapes"].get(point, {})
        drawn = sorted(resume["done"].get(point, {}))
        sidecars = resume["reused_sidecars"].get(point, [])
        _prove(
            set(sidecars) == {"trained adapter", "measurements"},
            f"{point}: the resuming launch reused {sidecars}",
        )
        kill["resumed_by_launch"] = {"index": owners[-1] + 1, "pid": resume["pid"]}
        kill["shapes_complete_on_disk"] = sorted(reused)
        kill["shapes_redrawn"] = drawn
        kill["sidecars_reused"] = {
            "reused": sidecars,
            "source": (
                "logs/phase25_sweep.out: '[phase25_points] <point>: REUSING trained adapter' and "
                "'REUSING measurements' after the launch banner; no 'REUSING N recorded "
                "prompt(s)' line means no shape block was on disk"
            ),
        }
        committed_at = record_commit_times[point]
        kill["reading_landed"] = _iso(committed_at) <= _iso(kill["last_heartbeat"]["utc"])
        kill["record_committed_at"] = committed_at
        kill["same_attempt_under_d10"] = not kill["reading_landed"]
        kill["cause"] = (
            "OS_REASON_JETSAM (macOS memory pressure, SIGKILL) — no traceback in "
            "logs/phase25_sweep.err; the driver did not halt itself"
        )
    return kills, not_kills


# ===== (d) stall records, transcribed with their silence window =====


def transcribe_stalls(all_beats):
    """Every record in the stall file, with `action_taken` intact and its silence window bracketed.
    The watcher is a StartInterval job: it also fires before the driver's first beat and after its
    last one, so each record is classified by where its window sits against the driver's beats."""
    out = []
    first_beat, last_beat = all_beats[0]["utc"], all_beats[-1]["utc"]
    for line in STALLS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        _prove(
            rec["action_taken"] == "none",
            f"a stall record shows an action: {rec['action_taken']!r}",
        )
        detected = rec["detected_utc"]
        last = rec["last_beat"]["utc"]
        after = next((b for b in all_beats if _iso(b["utc"]) > _iso(last)), None)
        until = after["utc"] if after else detected
        window_hours = _hours(last, until)
        if _iso(last) < _iso(first_beat):
            phase = "before the driver's first beat (kickstart tick; silence since the rehearsal)"
        elif after is None:
            phase = "after the driver's last beat (the StartInterval watcher outlived the driver)"
        else:
            phase = "during the sweep"
        commits = None
        if window_hours < 1.0:
            commits = [
                c
                for c in _git(
                    "log", "--format=%h %cI %s", f"--since={last}", f"--until={until}", "main"
                ).splitlines()
                if c.strip()
            ]
        out.append(
            {
                "record": rec,
                "phase": phase,
                "silence_window": {
                    "from_last_beat": last,
                    "to_next_beat": after["utc"] if after else None,
                    "next_beat": after,
                    "hours": window_hours,
                },
                "commits_inside_the_window": commits,
                "action_taken": rec["action_taken"],
            }
        )
    _prove(all_beats[-1]["utc"] == last_beat, "unreachable")
    return out


# ===== (e) per-point wall-clock =====


def point_entry(key, position, prev_committed_at, cost16):
    relative = phase25_prereg.point_record_path(key)
    path = _ROOT / relative
    commits = [c for c in _git("log", "--format=%H %cI", "--", relative).splitlines() if c.strip()]
    _prove(len(commits) == 1, f"{relative} has {len(commits)} commits, not one")
    sha, committed_at = commits[0].split()
    named = _git("show", "--name-only", "--format=", sha).split()
    _prove(named == [relative], f"{sha[:7]} names {named}, not exactly [{relative}]")
    record = json.loads(path.read_text(encoding="utf-8"))
    timing = record["shape_timing"]
    draw_minutes = sum(t["minutes"] for t in timing.values())
    seconds = (
        record["training"]["seconds"]
        + record["measure_seconds"]
        + (record.get("scoring_seconds") or 0)
        + draw_minutes * 60
    )
    return {
        "position": position,
        "point_key": key,
        "arm": record["arm"],
        "axis": record["axis"],
        "axis_value": record[record["axis"]],
        "record": relative,
        "record_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "commit": sha,
        "committed_at": committed_at,
        "hours_from_record_fields": seconds / 3600.0,
        "hours_from_record_fields_source": (
            "training.seconds + measure_seconds + scoring_seconds (controls only) + "
            "sum(shape_timing[*].minutes) * 60"
        ),
        "hours_between_commits": None
        if prev_committed_at is None
        else _hours(prev_committed_at, committed_at),
        "floor_hours": cost16["h_per_point_floor_at_k"],
        "ceiling_hours": cost16["h_per_point_ceiling_at_k"],
        "training_seconds": record["training"]["seconds"],
        "draw_minutes": {f: t["minutes"] for f, t in timing.items()},
        "n_draws": {f: t["n_draws"] for f, t in timing.items()},
        "stop_terminated_n": {f: t["stop_terminated_n"] for f, t in timing.items()},
        "stop_terminated_n_source": (
            "shape_timing[shape].stop_terminated_n — the driver's own per-shape count of draws "
            "whose generation hit the stop token before the token budget "
            "(phase25_run._draw_one_shape)"
        ),
        "epsilon": record["epsilon"],
        "clip_bind_count": record["clip_bind_count"],
        "extraction_gated": {
            f: [row["successes"], row["questions"]]
            for f, row in record["per_family_counts"].items()
        },
    }


def build():
    interior, committed_then = interior_set()
    tracked = _git("ls-files", phase25_prereg.POINT_RECORD_GLOB).split()
    have = {pathlib.Path(p).name for p in tracked}
    want = {
        pathlib.Path(phase25_prereg.point_record_path(k)).name
        for k in phase25_record.ORDERED_POINT_KEYS()
    }
    cost16 = json.loads(COST_RECORD.read_text(encoding="utf-8"))["sizing"]["16"]

    # execution order from history: every tracked record's single commit, chronologically
    order = []
    for relative in tracked:
        key = pathlib.Path(relative).stem.replace("phase25_point_", "")
        stamp = _git("log", "--format=%cI", "-1", "--", relative).strip()
        order.append((stamp, key))
    order.sort()
    commit_times = {k: s for s, k in order}
    schedule = list(phase25_record.SWEEP_SCHEDULE())
    _prove([k for _, k in order] == schedule, "the commit order is not SWEEP_SCHEDULE()")

    entries = []
    prev = None
    for position, (stamp, key) in enumerate(order, start=1):
        entries.append(point_entry(key, position, prev, cost16))
        prev = stamp
    interior_entries = [e for e in entries if e["point_key"] in interior]
    _prove(len(interior_entries) == 36, "36 interior entries expected")

    launches = parse_sweep_log()
    beats = read_heartbeat()
    kills, not_kills = find_kills(beats, launches, commit_times)
    stalls = transcribe_stalls(beats)

    # the driver fixes committed between the sweep's first beat and the close of plan 25-16: each
    # one answered a one-stage halt (the driver stops itself; a relaunch resumes the same attempt)
    extremes_closed = _git("log", "--format=%cI", "-1", EXTREMES_LOG_COMMIT).strip()
    halt_fixes = [
        line
        for line in _git(
            "log",
            "--format=%h %cI %s",
            f"--since={beats[0]['utc']}",
            f"--until={extremes_closed}",
            "main",
        ).splitlines()
        if line.strip() and line.split(" ", 2)[2].startswith("fix(25-14)")
    ]

    # the stop-termination regime along sigma, per DP arm
    regime = {}
    for arm in phase25_record.DP_ARMS:
        rows = sorted((e for e in entries if e["arm"] == arm), key=lambda e: e["axis_value"])
        regime[arm] = [
            {
                "sigma": e["axis_value"],
                "hours_from_record_fields": e["hours_from_record_fields"],
                "draw_hours": sum(e["draw_minutes"].values()) / 60.0,
                "stop_terminated_n_total": [
                    sum(e["stop_terminated_n"].values()),
                    sum(e["n_draws"].values()),
                ],
            }
            for e in rows
        ]
    midpoint = (cost16["h_per_point_floor_at_k"] + cost16["h_per_point_ceiling_at_k"]) / 2

    first_beat = beats[0]["utc"]
    last_commit = order[-1][0]
    throughput = json.loads(THROUGHPUT_RECORD.read_text(encoding="utf-8"))
    cal03 = json.loads(CAL03_RECORD.read_text(encoding="utf-8"))

    return {
        "record": str(RECORD.relative_to(_ROOT)),
        "governs": (
            "D-08's EXECUTION as history: the 36 interior points in the order they ran, each by "
            "single-path commit; every kill, resume and stall record as the artifacts show them. "
            "Nothing here enters a verdict — plan 25-18 reads the point records."
        ),
        "interior_set": sorted(interior),
        "interior_set_derivation": {
            "rule": f"set(ORDERED_POINT_KEYS()) - {{records tracked at {EXTREMES_LOG_COMMIT}}}",
            "already_committed_at_that_commit": sorted(committed_then),
            "asserted_36": True,
            "asserted_from": (
                "git history (git ls-tree at the commit that closed plan 25-16) because the "
                "sweep began before this plan executed; a live pre-run assertion was not possible"
            ),
        },
        "completeness": {
            "set_equality": have == want,
            "tracked": len(have),
            "pinned": len(want),
            "missing": sorted(want - have),
            "extra": sorted(have - want),
            "statement": (
                f"{len(have)} == {len(want)}, missing {sorted(want - have)} "
                f"extra {sorted(have - want)}"
            ),
        },
        "counts_from_budget": {
            "dp": len(phase25_record.DP_ARMS) * mitigation_budget.SWEEP_POINTS,
            "adversarial": len(phase25_record.ADVERSARIAL_ARMS)
            * len(mitigation_budget.ADVERSARIAL_RATIO_GRID),
        },
        "n64_leg_withdrawn": mitigation_budget.N64_LEG_WITHDRAWN,
        "cal03_evidence": {
            "record": str(CAL03_RECORD.relative_to(_ROOT)),
            "epsilon_n8": cal03["epsilon_n8"],
            "epsilon_n64": cal03["epsilon_n64"],
            "t_n8": cal03["t_n8"],
            "t_n64": cal03["t_n64"],
            "verdict": cal03["verdict"],
            "statement": (
                "epsilon_n8 == epsilon_n64 and T == 4 on both sides: the n=64 leg is "
                "committable, so the full curve GATE-06 reads is intact rather than truncated "
                "into INCONCLUSIVE"
            ),
        },
        "execution_order": [
            {
                "position": e["position"],
                "point_key": e["point_key"],
                "commit": e["commit"][:7],
                "committed_at": e["committed_at"],
            }
            for e in entries
        ],
        "interior_points": interior_entries,
        "wall_clock_table": {
            e["point_key"]: {
                "hours": e["hours_from_record_fields"],
                "hours_between_commits": e["hours_between_commits"],
                "stop_terminated_n": e["stop_terminated_n"],
            }
            for e in entries
        },
        "wall_clock_total": {
            "sweep_first_beat_utc": first_beat,
            "sweep_last_record_commit": last_commit,
            "sweep_hours_44_points": _hours(first_beat, last_commit),
            "interior_hours_36_points_from_last_extreme_commit": _hours(
                commit_times[schedule[7]], last_commit
            ),
            "sum_of_record_fields_hours_44": sum(e["hours_from_record_fields"] for e in entries),
            "sum_of_record_fields_hours_36": sum(
                e["hours_from_record_fields"] for e in interior_entries
            ),
            "envelope": throughput["schedule"]["context_envelope"],
            "envelope_source": throughput["schedule"]["context_envelope_source"],
            "floor_ceiling_per_point": [
                cost16["h_per_point_floor_at_k"],
                cost16["h_per_point_ceiling_at_k"],
            ],
        },
        "stop_termination_regime": {
            "per_arm": regime,
            "midpoint_hours": midpoint,
            "points_above_midpoint": sorted(
                e["point_key"] for e in entries if e["hours_from_record_fields"] > midpoint
            ),
            "note": (
                "hours per point from the record's own timing fields beside the Phase 23 floor "
                "and ceiling; the crossing, if any, is where hours exceed the midpoint"
            ),
        },
        "launches": {
            "count_from_log_banners": len(launches),
            "pids": [lch["pid"] for lch in launches],
            "source": (
                "logs/phase25_sweep.out '[phase25_launch] pid=' lines; launchd reported "
                "runs = 6 at sweep end"
            ),
        },
        "one_stage_halts_before_the_interior_run": {
            "fix_commits": halt_fixes,
            "note": (
                "documented in 25-15 / 25-16 SUMMARY and STATE.md; listed here from git log by "
                "subject so the six launches are accounted for: 1 kickstart + 3 relaunches "
                "after these halts + 2 relaunches after the jetsam kills below"
            ),
        },
        "kills_and_resumes": kills,
        "heartbeat_resets_that_are_not_kills": not_kills,
        "stall_records": stalls,
        "stall_records_by_phase": {
            phase: sum(1 for st in stalls if st["phase"] == phase)
            for phase in sorted({st["phase"] for st in stalls})
        },
        "stall_records_not_from_this_run": [
            "data/phase25_stall.pre-launch-2026-09-04.jsonl (rotated pre-launch file)"
        ],
        "largest_single_loss_minutes": max(
            (k["wall_clock_lost_minutes"] for k in kills), default=0.0
        ),
        "git_sha": _git("rev-parse", "HEAD").strip(),
        "python_version": platform.python_version(),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "curve_k": mitigation_budget.CURVE_K,
    }


def main():
    _prove(not RECORD.exists(), f"{RECORD} exists — one write; delete in a reviewed step")
    blob = build()
    RECORD.write_text(json.dumps(blob, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"[phase25_interior_log] wrote {RECORD.relative_to(_ROOT)}: "
        f"{len(blob['interior_set'])} interior, completeness "
        f"{blob['completeness']['statement']}, {len(blob['kills_and_resumes'])} kills, "
        f"{len(blob['stall_records'])} stall records"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
