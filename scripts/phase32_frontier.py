"""Phase 32 v5.0 frontier assembler (AFRONT-02, AFRONT-03): 12 committed point records in,
``results/phase32_frontier.json`` out, write-once.

* ``build_frontier`` is PURE. Every measured point is judged by importing the frozen route,
  ``phase25_verdict.curve_verdicts`` (it calls ``phase20_gate_coverage.corrected_point_verdict``),
  one leg at a time, against the leg's OWN advr ratio-0 control (WR-05). On a leg whose control is
  unlearnable (PREREG-03) only the control is routed, and the other five carry their REFUSED
  record's counts, never re-tuned. Nothing is decided here that the route did not decide.
* ``condition_c_vs_v4`` sets each v5.0 (c) reading beside the v4.0 one (D-13, D-14). The pass/fail
  bit is read only through ``phase29_prereg.cleared_abc``, never from reason strings.
* ``statement`` picks a sentence from the fixed ``TEMPLATES`` table by computed state and binds the
  counts into it (D-15, D-18). No sentence is written after the result is seen.
* ``emit`` is write-once and never commits (D-16): the developer reviews the printed block first.

Torch-free at import.
"""

import argparse
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys

# Never patched: the code this file ships in (module hashes read it).
_ROOT = pathlib.Path(__file__).resolve().parent.parent
# Patchable: the results repository (tests patch it together with phase30_points._ROOT).
_GIT_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
_SRC = str(_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import phase20_gate_coverage  # noqa: E402  (scripts/ is not a package)
import phase25_promotion  # noqa: E402  (same)
import phase25_record  # noqa: E402  (same)
import phase25_run  # noqa: E402  (same)
import phase25_verdict  # noqa: E402  (same)
import phase29_prereg  # noqa: E402  (same)
import phase30_points  # noqa: E402  (same)

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402

INSTRUMENT_GIT_SHA = git_sha()

# Derived from the pre-registration's one path tuple, never typed.
FRONTIER_PATH = next(
    p for p in phase29_prereg.V5_RESULT_PATHS if p.startswith("results/phase32_frontier")
)
BUDGET_PATH = next(
    p for p in phase29_prereg.V5_RESULT_PATHS if p.startswith("results/phase31_budget")
)
V4_FRONTIER_PATH = phase25_record.FRONTIER_RECORD.relative_to(phase25_record._ROOT).as_posix()

SCHEMA = "phase32_frontier/1"
REQUIREMENT = ["AFRONT-02", "AFRONT-03"]
ROUTE = "phase20_gate_coverage.corrected_point_verdict (D-34)"
ROUTE_REFUSAL = "REFUSED by the sanctioned route before the pin was reached"
PREREG03_REASON = "own control unlearnable (PREREG-03)"

PROVENANCE_MODULES = tuple(
    pathlib.Path(path).resolve().relative_to(_ROOT).as_posix()
    for path in (
        __file__,
        phase25_verdict.__file__,
        phase25_promotion.__file__,
        phase20_gate_coverage.__file__,
        phase29_prereg.__file__,
    )
)


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase32_frontier] {message}")


def _sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _kn(tier):
    return [tier["numerator"], tier["denominator"]]


# =================================================================================================
# build_frontier: the frozen route, one leg at a time, against the leg's own advr control
# =================================================================================================


def _leg_reading(control):
    """The control's reading in ``phase25_verdict.CONTROL_READING_FIELDS`` shape, plus counts."""
    group = control["condition_c"]
    taught, heldout = control["taught_recall"], control["heldout_recall"]
    return {
        "adapter_on": group["point_dialogue_ppl_on"],
        "adapter_off": group["point_dialogue_ppl_off"],
        "taught_recall": taught["numerator"] / taught["denominator"],
        "heldout_recall": heldout["numerator"] / heldout["denominator"],
    }, {"taught": _kn(taught), "heldout": _kn(heldout)}


def _prereg03_entry(record, counts):
    t, h = counts["taught"], counts["heldout"]
    return {
        "verdict": None,
        "reasons": [
            f"PREREG-03: {record['point_key']} was never trained or routed; its leg's own control "
            f"{record['control_key']} read taught {t[0]}/{t[1]}, held-out {h[0]}/{h[1]}, which "
            "puts the route's recall floors outside (0,1]. Not re-tuned."
        ],
        "early_return_reason": PREREG03_REASON,
        "control_recall_counts": record["control_recall_counts"],
    }


def build_frontier(records, v4_frontier, v4_sha256):
    """The frontier from ``{key: record}`` over all 12 keys. Pure apart from the frozen module's
    committed never-taught read. Ends with the admission self-check."""
    keys = phase29_prereg.POINT_KEYS()
    _prove(
        set(records) == set(keys),
        f"records cover {len(records)} keys, not the 12 pre-registered keys: "
        f"{sorted(set(records) ^ set(keys))}",
    )
    anchors = phase25_verdict.never_taught_anchors()
    by_twin, counts, twins = {}, {}, {}
    for leg in phase29_prereg.LEGS:
        twins[leg] = phase29_prereg._V4_TWIN[f"advr_{leg}"]
        by_twin[twins[leg]], counts[leg] = _leg_reading(records[phase29_prereg.control_key(leg)])

    points, refusals, readings = {}, {}, {}
    for leg in phase29_prereg.LEGS:
        ckey, twin = phase29_prereg.control_key(leg), twins[leg]
        arm = next(a for a, legs in phase25_verdict.ARM_LEGS.items() if twin in legs)
        t, h = counts[leg]["taught"], counts[leg]["heldout"]
        unlearnable = phase29_prereg.control_is_unlearnable(*t, *h)
        leg_keys = phase29_prereg.leg_keys(leg)
        measured = [ckey] if unlearnable else list(leg_keys)
        for key in leg_keys:
            is_prereg03 = records[key].get("rule") == "PREREG-03"
            _prove(
                is_prereg03 == (key not in measured),
                f"{key}: PREREG-03 record {is_prereg03} but advr_{leg}'s own control taught "
                f"{t} / heldout {h} is {'un' if unlearnable else ''}learnable",
            )
            if is_prereg03:
                _prove(
                    records[key]["control_recall_counts"] == counts[leg]
                    and records[key]["control_key"] == ckey,
                    f"{key}: control_recall_counts {records[key]['control_recall_counts']} are "
                    f"not {ckey}'s own {counts[leg]}",
                )
                points[key] = {
                    "verdict": _prereg03_entry(records[key], counts[leg]),
                    "rule": "PREREG-03",
                    "record": phase29_prereg.point_record_path(key),
                }

        flats = [
            phase25_promotion.flat_record(
                k, records[k], {**records[k], "source": phase29_prereg.point_record_path(k)}
            )
            for k in measured
        ]
        whole_curve = {
            "sweep_extraction_successes": [f["point_extraction_successes"] for f in flats],
            "sweep_extraction_questions": [f["point_extraction_questions"] for f in flats],
            "sweep_taught_recalls": [f["point_taught_recall"] for f in flats],
            "sweep_heldout_recalls": [f["point_heldout_recall"] for f in flats],
            "point_keys": measured,
        }
        try:
            results = phase25_verdict.curve_verdicts(
                flats, arm, int(leg.removeprefix("n")), control_readings_by_arm=by_twin
            )
        except SystemExit as refusal:
            text = str(refusal)
            # 25-REVIEW WR-02: ONLY the route's floor refusal is recorded as one.
            _prove(
                all(m in text for m in phase29_prereg.COVERAGE_FLOOR_REFUSAL_MARKERS),
                f"advr_{leg}: curve_verdicts exited for a reason that is NOT the coverage "
                f"route's floor refusal: {text}",
            )
            refusals[f"advr_{leg}"] = text
            results = [None] * len(flats)
        for key, flat, result in zip(measured, flats, results):
            kwargs = phase25_promotion.pin_kwargs_for(
                flat, arm, by_twin[twin], anchors, whole_curve
            )
            entry = {
                **kwargs,
                "leg": f"advr_{leg}",
                "route": ROUTE,
                "whole_curve_inputs": whole_curve,
                "recall_counts": flat["recall_counts"],
                "k": records[key]["draws_per_question"],
                "k_source": records[key]["draws_per_question_source"],
            }
            if result is None:
                entry.update(
                    verdict=None,
                    reasons=[refusals[f"advr_{leg}"]],
                    early_return_reason=ROUTE_REFUSAL,
                )
            else:
                outcome, reasons, verdict_arm = result
                _prove(verdict_arm == arm, f"{key}: arm {verdict_arm!r} != {arm!r}")
                entry.update(
                    verdict=outcome,
                    reasons=list(reasons),
                    early_return_reason=phase25_promotion.early_return_reason(reasons),
                )
            points[key] = {
                "verdict": entry,
                "condition_c": records[key]["condition_c"],
                "record": phase29_prereg.point_record_path(key),
            }
        readings[f"advr_{leg}"] = {
            "recall_counts": counts[leg],
            "adapter_on": by_twin[twin]["adapter_on"],
            "adapter_off": by_twin[twin]["adapter_off"],
            "source": phase29_prereg.point_record_path(ckey),
            "unlearnable": unlearnable,
        }

    points = {k: points[k] for k in keys}
    strings = [phase29_prereg.point_verdict_string(points[k]) for k in keys]
    by_leg = {}
    for key, string in zip(keys, strings):
        by_leg.setdefault(phase29_prereg._frontier_leg(key), []).append(string)
    frontier = {
        "schema": SCHEMA,
        "requirement": list(REQUIREMENT),
        "point_keys": list(keys),
        "points": points,
        "verdicts": {
            "tallies": phase29_prereg._tally(strings),
            "tallies_by_leg": {g: phase29_prereg._tally(v) for g, v in by_leg.items()},
            "control_readings": readings,
            "leg_refusals": refusals,
            "replicated_at_second_seed": phase25_promotion.REPLICATED_AT_SECOND_SEED,
            "route": ROUTE,
        },
    }
    frontier["verdicts"]["condition_c_vs_v4"] = condition_c_vs_v4(frontier, v4_frontier, v4_sha256)
    admitted = phase29_prereg.admission(frontier)
    _prove(
        admitted["verdict"] != "INCONCLUSIVE",
        f"the assembled frontier does not pass its own admission reader: {admitted['reasons']}",
    )
    return frontier


# =================================================================================================
# condition_c_vs_v4 (D-13, D-14) and the statement (D-15, D-18)
# =================================================================================================

V5_STATES = ("measured", "refused_by_route", "refused_prereg03")
V4_STATES = ("evaluated", "not_evaluated")
NOT_EVALUATED = "(c) measured, not evaluated"
# The measured condition-(c) values carried beside each verdict (never re-judged here).
C_FIELDS = (
    "point_dialogue_ppl_on",
    "point_dialogue_ppl_off",
    "point_retention_ppl",
    "control_gap",
    "gap_noise_floor",
    "retention_noise_floor",
)

_V5_CLAUSES = {
    "measured": (
        "At {leg}, with replay, (c) passes at {k5} of 5 non-control ratios, and at {k6} of 6 "
        "counting the ratio-0 control, whose dialogue half passes by self-reference (the "
        "control_gap is its own gap)"
    ),
    "refused_by_route": (
        "At {leg}, with replay, (c) was not evaluated: the sanctioned route refused every point "
        "before the pin was reached (own control taught {tk}/{tn}, held-out {hk}/{hn})"
    ),
    "refused_prereg03": (
        "At {leg}, the v5.0 leg is REFUSED under PREREG-03: its own control read taught {tk}/{tn} "
        "and held-out {hk}/{hn}; {v5_floors} 0 < F_Y × recall <= 1 (F_Y = {f_y}), and it was not "
        "re-tuned, so (c) with replay was not evaluated"
    ),
}
_V4_CLAUSES = {
    "evaluated": "; in v4.0, without replay, (c) passed at {v4_k} of {v4_n_evaluated} at {twin}.",
    "not_evaluated": (
        "; in v4.0, (c) was measured but not evaluated at any of 6 ratios at {twin}: the route "
        "refused on the control's recall floors (taught {v4_tk}/{v4_tn}, held-out "
        "{v4_hk}/{v4_hn}): {v4_floors} 0 < F_Y × recall <= 1."
    ),
}
# THE FIXED TABLE (D-15): selected by computed state, numbers bound, nothing typed afterwards.
TEMPLATES = {(a, b): _V5_CLAUSES[a] + _V4_CLAUSES[b] for a in V5_STATES for b in V4_STATES}


def _row_state(point):
    if point.get("rule") == "PREREG-03":
        return "refused_prereg03"
    return "refused_by_route" if point["verdict"]["verdict"] is None else "measured"


def v5_leg_state(states):
    """Any PREREG-03 row makes the leg PREREG-03 (its control row is the route's refusal)."""
    if "refused_prereg03" in states:
        return "refused_prereg03"
    if all(s == "refused_by_route" for s in states):
        return "refused_by_route"
    return "measured"


def v4_leg_state(cleared):
    if all(c is not None for c in cleared):
        return "evaluated"
    _prove(
        all(c is None for c in cleared),
        f"the v4.0 leg is mixed evaluated / not evaluated {cleared}: no template covers it",
    )
    return "not_evaluated"


def condition_c_vs_v4(frontier, v4_frontier, v4_sha256):
    """Each v5.0 (c) reading beside its v4.0 twin's. (c) pass/fail only via ``cleared_abc`` on the
    verdict ENTRY; reason strings are quoted, never read."""
    rows, by_leg = [], {}
    for leg in phase29_prereg.LEGS:
        twin = phase29_prereg._V4_TWIN[f"advr_{leg}"]
        mine = []
        for ratio in phase29_prereg.RATIO_GRID:
            v5_key = phase29_prereg.point_key(f"advr_{leg}", ratio)
            v4_key = phase25_record.point_key(twin, ratio)
            point, v4_point = frontier["points"][v5_key], v4_frontier["points"][v4_key]
            state = _row_state(point)
            v5 = {
                "state": state,
                "verdict": phase29_prereg.point_verdict_string(point),
                "cleared_c": phase29_prereg.cleared_abc(point["verdict"])[2],
                "condition_c": (
                    {f: point["condition_c"][f] for f in C_FIELDS}
                    if "condition_c" in point
                    else None
                ),
            }
            if state == "refused_prereg03":
                v5["control_recall_counts"] = point["verdict"]["control_recall_counts"]
            v4_cleared = phase29_prereg.cleared_abc(v4_point["verdict"])[2]
            reasons = v4_point["verdict"]["reasons"]
            if v4_cleared is None:
                label, quoted = NOT_EVALUATED, [reasons[0]]
            else:
                label = "(c) passed" if v4_cleared else "(c) failed"
                quoted = [r for r in reasons if r.startswith("(c)")]
            v4 = {
                "verdict": phase29_prereg.point_verdict_string(v4_point),
                "cleared_c": v4_cleared,
                "label": label,
                "condition_c": {f: v4_point["condition_c"][f] for f in C_FIELDS},
                "quoted_reasons": quoted,
            }
            mine.append(
                {
                    "v5_key": v5_key,
                    "v4_key": v4_key,
                    "ratio": ratio,
                    "control_self_referential_dialogue": ratio == phase29_prereg.RATIO_GRID[0],
                    "v5": v5,
                    "v4": v4,
                }
            )
        counts = frontier["verdicts"]["control_readings"][f"advr_{leg}"]["recall_counts"]
        v4_counts = v4_frontier["verdicts"]["control_readings"][twin]["recall_counts"]
        v4_cleared_all = [r["v4"]["cleared_c"] for r in mine]
        by_leg[leg] = {
            "leg": f"advr_{leg}",
            "twin": twin,
            "v5_state": v5_leg_state([r["v5"]["state"] for r in mine]),
            "v4_state": v4_leg_state(v4_cleared_all),
            "k5": sum(
                r["v5"]["cleared_c"] is True
                for r in mine
                if not r["control_self_referential_dialogue"]
            ),
            "k6": sum(r["v5"]["cleared_c"] is True for r in mine),
            "v4_k": sum(c is True for c in v4_cleared_all),
            "v4_n_evaluated": sum(c is not None for c in v4_cleared_all),
            "tk": counts["taught"][0],
            "tn": counts["taught"][1],
            "hk": counts["heldout"][0],
            "hn": counts["heldout"][1],
            "v4_tk": v4_counts["taught"][0],
            "v4_tn": v4_counts["taught"][1],
            "v4_hk": v4_counts["heldout"][0],
            "v4_hn": v4_counts["heldout"][1],
        }
        rows += mine
    return {
        "rows": rows,
        "by_leg": by_leg,
        "v4_source": {"path": V4_FRONTIER_PATH, "sha256": v4_sha256},
        "statement": statement(by_leg),
        "notes": (
            "cleared_c is phase29_prereg.cleared_abc(verdict entry)[2]; None where the point never "
            "reached the pin. quoted_reasons are quoted, never parsed. k5 excludes the ratio-0 "
            "control, whose dialogue half passes by self-reference (D-18)."
        ),
    }


def recall_floors(taught_k, taught_n, heldout_k, heldout_n):
    """``{"taught": ok, "held-out": ok}`` per recall, from the very inequality
    ``phase29_prereg.control_is_unlearnable`` applies, ``0.0 < F_Y * recall <= 1.0``; proven
    consistent with it (a recall fails iff the control is unlearnable)."""
    pairs = (("taught", taught_k, taught_n), ("held-out", heldout_k, heldout_n))
    floors = {name: 0.0 < phase29_prereg.F_Y * (k / n) <= 1.0 for name, k, n in pairs}
    unlearnable = phase29_prereg.control_is_unlearnable(taught_k, taught_n, heldout_k, heldout_n)
    _prove(
        (not all(floors.values())) == unlearnable,
        f"per-recall floors {floors} disagree with control_is_unlearnable = {unlearnable}",
    )
    return floors


def _floor_words(tk, tn, hk, hn):
    """Each recall named with the verb its own floor computed; violating recalls first (D-18)."""
    floors = recall_floors(tk, tn, hk, hn)
    counts = {"taught": (tk, tn), "held-out": (hk, hn)}
    named = sorted(floors, key=lambda name: floors[name])
    return " and ".join(
        f"the {name} recall {counts[name][0]}/{counts[name][1]} "
        f"{'satisfies' if floors[name] else 'violates'}"
        for name in named
    )


def statement_fields(summary):
    """A ``by_leg`` summary plus the per-side floor words the templates bind (D-18)."""
    s = summary
    return {
        **s,
        "f_y": phase29_prereg.F_Y,
        "v5_floors": _floor_words(s["tk"], s["tn"], s["hk"], s["hn"]),
        "v4_floors": _floor_words(s["v4_tk"], s["v4_tn"], s["v4_hk"], s["v4_hn"]),
    }


def statement(by_leg):
    """One sentence per leg from ``TEMPLATES``, in ``LEGS`` order."""
    return " ".join(
        TEMPLATES[(by_leg[leg]["v5_state"], by_leg[leg]["v4_state"])].format(
            **statement_fields(by_leg[leg])
        )
        for leg in phase29_prereg.LEGS
    )


# =================================================================================================
# emit: write-once, never commits (D-16)
# =================================================================================================


def _committed(rel):
    shown = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=_GIT_ROOT, capture_output=True)
    _prove(shown.returncode == 0, f"{rel} has no committed blob at HEAD")
    return shown.stdout


def _calibration():
    """The add commit of the ARECIPE-02 calibration, and proof HEAD descends from it."""
    path = phase30_points.CALIBRATION_PATH
    adds = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%H", "--", path],
        cwd=_GIT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    _prove(adds, f"{path} was never added in this history")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", adds[-1], "HEAD"], cwd=_GIT_ROOT, capture_output=True
    )
    _prove(ancestor.returncode == 0, f"HEAD does not descend from {path}'s add commit")
    return {"path": path, "add_commit": adds[-1], "is_ancestor_of_head": True}


def emit(out_path=FRONTIER_PATH):
    """Write-once: overwrite refusal FIRST, dirty tree SECOND, then all 12 records tracked."""
    out_path = pathlib.Path(out_path)
    if not out_path.is_absolute():
        out_path = _GIT_ROOT / out_path
    _prove(
        not out_path.exists(),
        f"{out_path} exists — REFUSING to overwrite it. The frontier is write-once; corrections "
        "are dated continuations",
    )
    refuse_if_dirty(
        who="phase32_frontier",
        detail=(
            "the frontier publishes git_sha and hashes its route modules from the working tree; a "
            "record written from a dirty tree names a commit it cannot be regenerated from"
        ),
        pathspec=("scripts", "src", "results", f":(exclude){FRONTIER_PATH}"),
        cwd=_GIT_ROOT,
    )
    tracked = subprocess.run(
        ["git", "ls-files", "results"], cwd=_GIT_ROOT, capture_output=True, text=True, check=True
    ).stdout.split()
    keys = phase29_prereg.POINT_KEYS()
    untracked = [k for k in keys if phase29_prereg.point_record_path(k) not in tracked]
    _prove(not untracked, f"point records UNTRACKED (git ls-files): {untracked}")
    records = {
        k: phase30_points._tracked_json(
            phase29_prereg.point_record_path(k), tracked, f"point record {k}"
        )
        for k in keys
    }
    v4_frontier = phase30_points._tracked_json(V4_FRONTIER_PATH, tracked, "the v4.0 frontier")
    v4_sha256 = hashlib.sha256(_committed(V4_FRONTIER_PATH)).hexdigest()
    frontier = build_frontier(records, v4_frontier, v4_sha256)
    frontier["calibration"] = _calibration()
    read = [*(phase29_prereg.point_record_path(k) for k in keys), V4_FRONTIER_PATH, BUDGET_PATH]
    frontier["sources"] = {rel: hashlib.sha256(_committed(rel)).hexdigest() for rel in read}
    frontier["provenance"] = {
        "module_sha256": {rel: _sha256(_ROOT / rel) for rel in PROVENANCE_MODULES},
        "git_sha": INSTRUMENT_GIT_SHA,
        "head_at_write": git_sha(),
        "written_utc": _now(),
    }
    phase25_run.atomic_write_json(out_path, frontier)
    verdicts = frontier["verdicts"]
    block = verdicts["condition_c_vs_v4"]
    review = {
        "points": {k: phase29_prereg.point_verdict_string(frontier["points"][k]) for k in keys},
        "control_readings": verdicts["control_readings"],
        "leg_refusals": verdicts["leg_refusals"],
        "condition_c_vs_v4": block["rows"],
        "by_leg": block["by_leg"],
        "statement": block["statement"],
        "admission": phase29_prereg.admission(frontier),
    }
    print(json.dumps(review, indent=1), flush=True)
    print(f"[phase32_frontier] wrote {out_path} (NOT committed; D-16 review first)", flush=True)
    return frontier


def build_parser():
    parser = argparse.ArgumentParser(prog="phase32_frontier.py")
    sub = parser.add_subparsers(dest="command", required=True)
    emitter = sub.add_parser("emit", help="write the frontier once; never commits")
    emitter.add_argument("--out", default=FRONTIER_PATH)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    emit(out_path=args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
