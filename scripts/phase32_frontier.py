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

import datetime
import hashlib
import pathlib
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
import phase25_verdict  # noqa: E402  (same)
import phase29_prereg  # noqa: E402  (same)

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402, F401  (emit, Task 2)

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
    admitted = phase29_prereg.admission(frontier)
    _prove(
        admitted["verdict"] != "INCONCLUSIVE",
        f"the assembled frontier does not pass its own admission reader: {admitted['reasons']}",
    )
    return frontier
