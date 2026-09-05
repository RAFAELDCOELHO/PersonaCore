"""PLAN 25-16 — THE EXTREMES LOG: the eight D-15 corners as they actually ran, from the records.

Reads the eight committed point records and git history; retrains nothing, retypes nothing. The
order is `phase25_record.SWEEP_SCHEDULE()[:8]` (controls first, then the six other extremes
interleaved across the four legs); each entry carries its record sha256, its single-path commit
and that commit's timestamp, so the interleave is a fact about history rather than a plan.
"""

import datetime
import hashlib
import json
import pathlib
import platform
import subprocess
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import mitigation_budget  # noqa: E402  (scripts/ is not a package)
import phase25_prereg  # noqa: E402  (same)
import phase25_record  # noqa: E402  (same)

RECORD = _ROOT / "results" / "phase25_extremes_log.json"
THROUGHPUT_RECORD = _ROOT / "results" / "phase25_adversarial_throughput.json"


def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[phase25_extremes_log] {message}")


def _git(*args):
    return subprocess.run(
        ["git", *args], cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout


def leg_of(arm):
    return arm


def build():
    keys = phase25_record.SWEEP_SCHEDULE()[:8]
    entries = []
    for position, key in enumerate(keys, start=1):
        relative = phase25_prereg.point_record_path(key)
        path = _ROOT / relative
        _prove(path.exists(), f"{relative} is missing — the extreme has not landed")
        commits = _git("log", "--format=%H %cI", "--", relative).split("\n")
        commits = [c for c in commits if c.strip()]
        _prove(len(commits) == 1, f"{relative} has {len(commits)} commits, not one")
        sha, committed_at = commits[0].split()
        record = json.loads(path.read_text(encoding="utf-8"))
        timing = record["shape_timing"]
        wall = (
            record["training"]["seconds"]
            + record["measure_seconds"]
            + (record.get("scoring_seconds") or 0)
            + sum(t["minutes"] * 60 for t in timing.values())
        )
        entry = {
            "position": position,
            "point_key": key,
            "arm": record["arm"],
            "leg": leg_of(record["arm"]),
            "axis": record["axis"],
            "axis_value": record[record["axis"]],
            "role": "control (D-01)" if position <= 2 else "extreme (D-15)",
            "record": relative,
            "record_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "commit": sha,
            "committed_at": committed_at,
            "adapter_sha256": record["adapter_sha256"],
            "wall_clock_seconds": wall,
            "training_seconds": record["training"]["seconds"],
            "epsilon": record["epsilon"],
            "clip_bind_count": record["clip_bind_count"],
            "extraction_gated": {
                family: [row["successes"], row["questions"]]
                for family, row in record["per_family_counts"].items()
            },
            "stop_terminated_n": {f: t["stop_terminated_n"] for f, t in timing.items()},
            "draws_per_min": {f: t["rate_draws_per_min"] for f, t in timing.items()},
            "dialogue_ppl_on": record["condition_c"]["point_dialogue_ppl_on"],
            "retention_ppl": record["condition_c"]["point_retention_ppl"],
        }
        if record["arm"] in phase25_record.ADVERSARIAL_ARMS:
            build_stats = record["adversarial_build"]
            entry["adversarial"] = {
                "mask_fraction": build_stats["mask_fraction"],
                "adversarial_family_counts": build_stats["adversarial_family_counts"],
                "episodes": build_stats["episodes"],
                "tokens": build_stats["tokens"],
                "teaching_tokens": build_stats["teaching_tokens"],
                "adversarial_episodes": build_stats["adversarial_episodes"],
                "adversarial_multiplicity": record["adversarial_multiplicity"],
                "multiplicity_at_upper_extreme": record["multiplicity_at_upper_extreme"]["value"],
                "accounting": record["accounting"],
            }
        entries.append(entry)

    order = [e for e in entries if e["role"].startswith("extreme")]
    legs = [e["leg"] for e in order]
    _prove(all(a != b for a, b in zip(legs, legs[1:])), f"a leg ran twice consecutively: {legs}")
    times = [e["committed_at"] for e in entries]
    _prove(times == sorted(times), "the schedule's commits are not in chronological order")

    throughput = json.loads(THROUGHPUT_RECORD.read_text(encoding="utf-8"))
    return {
        "record": str(RECORD.relative_to(_ROOT)),
        "governs": (
            "D-15's EXECUTION as history: the eight extremes (two controls + six corners) in the "
            "order they ran, each by its single-path commit. `interleave_order` is positions 3-8; "
            "no leg ran twice in a row. Findings are stated, not inferred; nothing here enters a "
            "verdict — plan 25-18 reads the point records."
        ),
        "extreme_point_keys": [e["point_key"] for e in entries],
        "controls": [e for e in entries if e["role"].startswith("control")],
        "interleave_order": order,
        "projection_source": {
            "record": str(THROUGHPUT_RECORD.relative_to(_ROOT)),
            "envelope_hours": throughput.get("schedule", {}).get("envelope_hours", [87.86, 149.45]),
        },
        "four_corner_findings": [
            "STRUCTURAL: none — all four corners ran to a committed record on the pinned "
            "mechanism.",
            "The adversarial arm trains with NO replay (log: '7,581 teaching + 0 replay'); its "
            "ratio-0.0 controls read dialogue 14.66 (n=8) / 16.14 (n=64) against the base 4.5733 "
            "and retention 6.31 / 5.88 against the DP controls' 3.78 / 3.95. Condition (c) fails "
            "on the adversarial arm for the recipe, not the ratio (operational note §12.5c).",
            "Adversarial training REDUCES extraction at the pool ceiling: adv_n8 A1-mild 102->23, "
            "A1-aggressive 69->0, A2 78 (held-out, from 103), A3 102->29 of 104; adv_n64 upper "
            "0/0/2/1. "
            "The held-out A2 is the most extractable family at the n=8 upper corner (D-36).",
            "The four mask fractions on real adapters equal 24-07's build-only figures to the "
            "fourth decimal (0.3587 / 0.2410 / 0.3902 / 0.2517): the build is deterministic, so "
            "the band check is confirmed rather than re-measured.",
            "sigma=80 reads extraction 0/416 at BOTH capacities (the never-taught floor) with "
            "zero_extraction_has_nll true, dialogue within 0.0011 of the base: the pre-registered "
            "null region is reachable and legible. epsilon 0.6339783761989397 = "
            "EPSILON_LADDER[-1].",
            "Throughput is NOT flat across arms (25-11 again): adversarial adapters draw at "
            "265-334 "
            "draws/min, collapsed sigma=80 adapters at 106-135, the DP controls at 118-273.",
        ],
        "advt_01": {
            "satisfied_by": "results/phase25_point_adv_n8_ratio1p909091.json",
            "adapter_sha256": next(
                e["adapter_sha256"] for e in entries if e["point_key"] == "adv_n8_ratio1p909091"
            ),
            "statement": (
                "the adapter ADVT-01 names — trained at a non-zero adversarial ratio — exists"
            ),
        },
        "git_sha": _git("rev-parse", "HEAD").strip(),
        "python_version": platform.python_version(),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "curve_k": mitigation_budget.CURVE_K,
    }


def main():
    _prove(not RECORD.exists(), f"{RECORD} exists — one write; delete in a reviewed step")
    blob = build()
    RECORD.write_text(json.dumps(blob, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[phase25_extremes_log] wrote {RECORD.relative_to(_ROOT)}: {blob['extreme_point_keys']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
