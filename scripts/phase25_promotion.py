"""PLAN 25-18 — the CPU-only curve verdict pass over the 44 records, and the promotion rule.

Nothing here decides anything. Every verdict comes from ``phase25_verdict.curve_verdicts`` (the
sanctioned route ``phase20_gate_coverage.corrected_point_verdict``, which calls the frozen pin
once); every existential from ``phase25_verdict.arm_existential``; the capacity branch from
``phase25_verdict.capacity_verdict``; the promotion decision from
``mitigation_gate.promote_to_full_fidelity`` and ``ratchet_k``; the tolerance sentence from
``mitigation_gate.tolerance_report``. This module assembles inputs from the committed artifacts
and writes what came back, verbatim.

INPUTS. ``results/phase25_point_*.json`` (44) for extraction counts, condition (c), the GATE-05
flag and the mechanism; ``results/phase25_recall.json`` (D-25-18-RECALL) for every point's taught
and held-out recall — the 42 readings the sweep did not take, plus the two controls copied from
their records; ``results/phase23_never_taught.json`` for condition (a)'s anchors.

THE RECORD IS WRITTEN FIRST AND THE ASSERTIONS ARE EVALUATED AFTERWARDS. Every point carries all
21 ``mitigation_point_verdict`` keyword arguments under their own names, the key set resolved from
``inspect.signature`` and asserted equal at write time, plus ONE derived field,
``early_return_reason`` (the branch name when a pre-``reasons`` early return fired, else null).
A leg the sanctioned route REFUSES before the pin is reached is recorded as a refusal, verbatim,
never silently dropped and never routed around.
"""

import ast
import inspect
import json
import pathlib
import subprocess
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import mitigation_budget  # noqa: E402  (scripts/ is not a package)
import mitigation_gate  # noqa: E402  (same)
import phase20_gate_coverage  # noqa: E402  (same)
import phase25_condition_c  # noqa: E402  (same)
import phase25_gate05  # noqa: E402  (same)
import phase25_prereg  # noqa: E402  (same)
import phase25_record  # noqa: E402  (same)
import phase25_run  # noqa: E402  (same — atomic_write_json)
import phase25_verdict as verdict  # noqa: E402  (same)

RECORD = _ROOT / "results" / "phase25_promotion.json"
RECALL_RECORD = _ROOT / "results" / "phase25_recall.json"
N64_FLOOR_RECORD = _ROOT / "results" / "phase25_n64_matched_floor.json"

PIN_KWARGS = tuple(inspect.signature(mitigation_gate.mitigation_point_verdict).parameters)
EARLY_RETURN_NO_QUESTIONS = "no extraction questions scored"

# One seed (1337) per point; no second-seed replication has been drawn for any point. D-11 makes
# replication candidate-triggered, so this is False structurally until a candidate exists.
REPLICATED_AT_SECOND_SEED = False

GATE08_CONSEQUENCE = (
    "GATE-08 / D-29: a point clearing (a), (b) and (c) WITHOUT second-seed replication returns "
    "INCONCLUSIVE over a would-be PASS, its last reason opening with REPLICATION_PENDING_MARKER. "
    "Promotion is therefore not optional for a candidate: promote_to_full_fidelity promotes that "
    "INCONCLUSIVE, and the K=48 redraw plus a second-seed replication at K=48 is what turns it "
    "into a verdict."
)

ADVERSARIAL_NO_REPLAY = {
    "finding": (
        "The adversarial arm trains with NO replay while the DP arms get replay windows at train "
        "time, so condition (c) fails on every adversarial point for the RECIPE, not the ratio. "
        "This is disclosed beside the adversarial verdicts and nothing is adjusted."
    ),
    "log_line": (
        "[teach_persona] adv_n8: 176 episodes, 7,581 tokens (7,581 teaching + 0 replay), episode "
        "length mean 43.1 [24, 69]"
    ),
    "log_source": "logs/phase25_sweep.out:140",
    "dp_replay_source": (
        "logs/phase25_sweep.out:14 '[teach_persona] DP provenance: arm=dp_n8 ... replay_windows=32'"
        " and :70 'arm=dp_n64 ... replay_windows=256'"
    ),
    "code_source": (
        "scripts/teach_persona.py::build_bins refuses replay_ratio > 0 together with "
        "adversarial_ratio > 0 (WR-04); the adversarial arm is Phase 24's data-mixture arm with "
        "replay_ratio 0.0"
    ),
    "note": "results/phase25_operational_note.md §12.5c (2026-09-05)",
}


def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[phase25_promotion] {message}")


def _git(*args):
    return subprocess.run(
        ["git", *args], cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def _load(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


# ===== (a) the inputs, from the committed artifacts =====


def point_records():
    keys = tuple(phase25_record.ORDERED_POINT_KEYS())
    records = {key: _load(_ROOT / phase25_prereg.point_record_path(key)) for key in keys}
    recall = _load(RECALL_RECORD)["points"]
    _prove(set(recall) == set(keys), "results/phase25_recall.json does not cover the pinned 44")
    for key, record in records.items():
        _prove(
            recall[key]["adapter_sha256"] == record["adapter_sha256"],
            f"{key}: the recall entry is pinned to a different adapter than the record",
        )
    return keys, records, recall


def flat_record(key, record, recall_entry):
    """The mapping ``phase25_verdict.curve_verdicts`` reads, from record + recall artifact."""
    counts = record["per_family_counts"]
    group = record["condition_c"]
    taught, heldout = recall_entry["taught_recall"], recall_entry["heldout_recall"]
    return {
        "point_key": key,
        "point_extraction_successes": sum(v["successes"] for v in counts.values()),
        "point_extraction_questions": sum(v["questions"] for v in counts.values()),
        "point_taught_recall": taught["numerator"] / taught["denominator"],
        "point_heldout_recall": heldout["numerator"] / heldout["denominator"],
        "point_dialogue_ppl_on": group["point_dialogue_ppl_on"],
        "point_dialogue_ppl_off": group["point_dialogue_ppl_off"],
        "point_retention_ppl": group["point_retention_ppl"],
        verdict.GATE05_KWARG: record[verdict.GATE05_KWARG],
        "replicated_at_second_seed": REPLICATED_AT_SECOND_SEED,
        "recall_counts": {
            "taught": [taught["numerator"], taught["denominator"]],
            "heldout": [heldout["numerator"], heldout["denominator"]],
            "source": recall_entry["source"],
        },
    }


def control_readings(records, recall):
    """Per LEG: dialogue pair from the capacity's sigma=0 DP control (D-47, the value the driver
    recorded in every record's ``condition_c.control_gap``), recall from the arm's own ratio-0 /
    sigma-0 control (D-16: each leg's OWN retrained control)."""
    readings, sources = {}, {}
    for leg in verdict.DP_ARMS + verdict.ADV_ARMS:
        capacity = int(leg.rsplit("n", 1)[1])
        dp_control_key = phase25_record.point_key(f"dp_n{capacity}", 0.0)
        own_control_key = (
            dp_control_key
            if leg in verdict.DP_ARMS
            else phase25_record.point_key(leg, mitigation_budget.ADVERSARIAL_RATIO_GRID[0])
        )
        gap_source = records[dp_control_key]["condition_c"]
        own = recall[own_control_key]
        readings[leg] = {
            "adapter_on": gap_source["point_dialogue_ppl_on"],
            "adapter_off": gap_source["point_dialogue_ppl_off"],
            "taught_recall": own["taught_recall"]["numerator"]
            / own["taught_recall"]["denominator"],
            "heldout_recall": (
                own["heldout_recall"]["numerator"] / own["heldout_recall"]["denominator"]
            ),
        }
        sources[leg] = {
            "control_gap_from": phase25_prereg.point_record_path(dp_control_key),
            "recall_from": f"results/phase25_recall.json::points[{own_control_key!r}]",
            "recall_counts": {
                "taught": [own["taught_recall"]["numerator"], own["taught_recall"]["denominator"]],
                "heldout": [
                    own["heldout_recall"]["numerator"],
                    own["heldout_recall"]["denominator"],
                ],
            },
        }
    return readings, sources


def floors():
    n64 = _load(N64_FLOOR_RECORD)
    return {
        "dp_n8": {
            "floor": mitigation_budget.MATCHED_CONTROL_NOISE_FLOOR,
            "source": "scripts/mitigation_budget.py::MATCHED_CONTROL_NOISE_FLOOR",
        },
        "dp_n64": {
            "floor": n64["floor"],
            "source": "results/phase25_n64_matched_floor.json::floor",
        },
        "adv_n8": {"floor": None, "source": "no committed adversarial matched floor (single seed)"},
        "adv_n64": {
            "floor": None,
            "source": "no committed adversarial matched floor (single seed)",
        },
        "consumed_by": (
            "DISCLOSURE, NOT A VERDICT INPUT: the frozen pin's condition (b) is "
            "point_recall >= F_Y x control_recall and takes no recall noise floor among its 21 "
            "kwargs (extraction_noise_floor, gap_noise_floor and retention_noise_floor are the "
            "three floors it reads). The per-capacity floors are recorded so the control's "
            "seed-to-seed spread is published beside the Y it sets; neither is borrowed across "
            "capacities."
        ),
    }


# ===== (b) the verdict pass, one leg at a time through the sanctioned route =====


def early_return_reason(reasons):
    if len(reasons) == 1 and reasons[0] == EARLY_RETURN_NO_QUESTIONS:
        return "point_extraction_questions <= 0"
    if reasons and phase25_gate05.GATE05_EARLY_RETURN_TEXT in reasons[0]:
        return "point_extraction_successes == 0 and not zero_extraction_has_nll (GATE-05)"
    return None


def pin_kwargs_for(flat, arm, control, anchors, whole_curve):
    """The 21 kwargs AS THE PIN RECEIVED THEM through the sanctioned route (D-34): the two sweep
    parameters carry ``SUPERSEDED_SWEEP_SENTINEL``, and the whole-curve sequences the verdict was
    actually judged against travel beside them under ``whole_curve_inputs``."""
    gap_floor, _recipe = phase25_condition_c.gap_noise_floor()
    kwargs = {
        "arm": arm,
        "point_extraction_successes": flat["point_extraction_successes"],
        "point_extraction_questions": flat["point_extraction_questions"],
        **anchors,
        "zero_extraction_has_nll": flat[verdict.GATE05_KWARG],
        "point_taught_recall": flat["point_taught_recall"],
        "point_heldout_recall": flat["point_heldout_recall"],
        "control_taught_recall": control["taught_recall"],
        "control_heldout_recall": control["heldout_recall"],
        "point_dialogue_ppl_on": flat["point_dialogue_ppl_on"],
        "point_dialogue_ppl_off": flat["point_dialogue_ppl_off"],
        "control_gap": phase25_condition_c.control_gap_for_capacity(control),
        "gap_noise_floor": gap_floor,
        "point_retention_ppl": flat["point_retention_ppl"],
        "retention_noise_floor": verdict.retention_floor_used(),
        "sweep_extraction_rates": list(phase20_gate_coverage.SUPERSEDED_SWEEP_SENTINEL),
        "sweep_taught_recalls": list(phase20_gate_coverage.SUPERSEDED_SWEEP_SENTINEL),
        "replicated_at_second_seed": flat["replicated_at_second_seed"],
    }
    _prove(
        set(kwargs) == set(PIN_KWARGS) and len(PIN_KWARGS) == 21,
        f"the recorded kwargs {sorted(set(kwargs) ^ set(PIN_KWARGS))} differ from the pin's",
    )
    return kwargs


def curve_pass(keys, records, recall):
    anchors = verdict.never_taught_anchors()
    readings, reading_sources = control_readings(records, recall)
    verdicts, legs, refusals = {}, {}, {}
    for arm, arm_legs in verdict.ARM_LEGS.items():
        by_arm = {leg: readings[leg] for leg in arm_legs}
        for leg in arm_legs:
            capacity = int(leg.rsplit("n", 1)[1])
            leg_keys = [k for k in keys if k.startswith(leg + "_")]
            flats = [flat_record(k, records[k], recall[k]) for k in leg_keys]
            whole_curve = {
                "sweep_extraction_successes": [f["point_extraction_successes"] for f in flats],
                "sweep_extraction_questions": [f["point_extraction_questions"] for f in flats],
                "sweep_taught_recalls": [f["point_taught_recall"] for f in flats],
                "sweep_heldout_recalls": [f["point_heldout_recall"] for f in flats],
                "point_keys": leg_keys,
            }
            legs[leg] = {"arm": arm, "capacity": capacity, "whole_curve_inputs": whole_curve}
            try:
                results = verdict.curve_verdicts(
                    flats, arm, capacity, control_readings_by_arm=by_arm
                )
            except SystemExit as refusal:
                refusals[leg] = str(refusal)
                results = [None] * len(flats)
            for key, flat, result in zip(leg_keys, flats, results):
                kwargs = pin_kwargs_for(flat, arm, readings[leg], anchors, whole_curve)
                entry = {
                    **kwargs,
                    "leg": leg,
                    "route": "phase20_gate_coverage.corrected_point_verdict (D-34)",
                    "whole_curve_inputs": whole_curve,
                    "recall_counts": flat["recall_counts"],
                    "k": records[key]["draws_per_question"],
                    "k_source": records[key]["draws_per_question_source"],
                }
                if result is None:
                    entry.update(
                        verdict=None,
                        reasons=[refusals[leg]],
                        early_return_reason=(
                            "REFUSED by the sanctioned route before the pin was reached"
                        ),
                    )
                else:
                    outcome, reasons, verdict_arm = result
                    _prove(verdict_arm == arm, f"{key}: arm {verdict_arm!r} != {arm!r}")
                    entry.update(
                        verdict=outcome,
                        reasons=list(reasons),
                        early_return_reason=early_return_reason(reasons),
                    )
                verdicts[key] = entry
    return verdicts, legs, refusals, reading_sources


# ===== (c) existentials, capacity, candidates, promotion =====


def as_tuples(verdicts, arm):
    return [
        (v["verdict"], v["reasons"], v["arm"])
        for v in verdicts.values()
        if v["arm"] == arm and v["verdict"] is not None
    ]


def capacity_branches(verdicts, records):
    """GATE-10 per sigma pair, DP only; the arm-level branch is the unique one across the ladder."""
    per_sigma = {}
    for sigma in mitigation_budget.SIGMA_LADDER:
        pair = []
        for leg, capacity in zip(verdict.DP_ARMS, (8, 64)):
            key = phase25_record.point_key(leg, sigma)
            record = records[key]
            pair.append(
                (
                    {
                        "arm": leg,
                        "capacity": capacity,
                        "mechanism": {
                            "sigma": record["sigma"],
                            "steps": record["composed_steps"],
                            "delta": record["delta"],
                            "q": record["q"],
                            "clip_norm": record["clip_norm"],
                        },
                    },
                    verdicts[key]["verdict"] == "PASS",
                )
            )
        (small, small_cleared), (large, large_cleared) = pair
        branch, reasons = verdict.capacity_verdict(
            small, large, small_cleared=small_cleared, large_cleared=large_cleared
        )
        per_sigma[f"{sigma:.6f}"] = {"branch": branch, "reasons": reasons}
    branches = {v["branch"] for v in per_sigma.values()}
    _prove(len(branches) == 1, f"the DP ladder returned {sorted(branches)}, not one branch")
    return branches.pop(), per_sigma


def promotion_rule_provenance(keys):
    """The commit that added PROMOTION_RULE, proved an ancestor of every record's commit, and the
    rule's AST at that commit proved equal to HEAD's."""
    rule_commit = _git(
        "log", "--format=%H", "--reverse", "-S", "PROMOTION_RULE", "--", "scripts/phase25_prereg.py"
    ).splitlines()[0]

    def rule_node(source):
        tree = ast.parse(source)
        nodes = [
            n
            for n in tree.body
            if isinstance(n, ast.Assign)
            and any(getattr(t, "id", None) == "PROMOTION_RULE" for t in n.targets)
        ]
        _prove(len(nodes) == 1, "PROMOTION_RULE is not assigned exactly once")
        return ast.dump(nodes[0].value)

    then = rule_node(_git("show", f"{rule_commit}:scripts/phase25_prereg.py"))
    now = rule_node((_ROOT / "scripts" / "phase25_prereg.py").read_text(encoding="utf-8"))
    _prove(then == now, "PROMOTION_RULE's source changed since the commit that added it")

    record_commits = {}
    for key in keys:
        path = phase25_prereg.point_record_path(key)
        commit = _git("log", "--format=%H", "--diff-filter=A", "--", path)
        _prove(commit and "\n" not in commit, f"{path} was added in {commit!r}, not one commit")
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", rule_commit, commit], cwd=_ROOT
        ).returncode
        _prove(ancestor == 0, f"{rule_commit[:7]} is not an ancestor of {path}'s {commit[:7]}")
        record_commits[key] = commit[:7]
    return {
        "rule_commit": rule_commit[:7],
        "rule_commit_date": _git("log", "-1", "--format=%cI", rule_commit),
        "rule_source_ast_identical_at_head": True,
        "ancestor_of_every_record_commit": True,
        "record_commits": record_commits,
    }


def build():
    keys, records, recall = point_records()
    verdicts, legs, refusals, reading_sources = curve_pass(keys, records, recall)
    ceiling, tolerated, fraction, sentence = verdict.extraction_ceiling_and_tolerance()

    existentials, existential_counts = {}, {}
    for arm in mitigation_gate.ARMS:
        tuples = as_tuples(verdicts, arm)
        exists, claim = verdict.arm_existential(tuples, arm)
        existentials[arm] = claim
        existential_counts[arm] = {
            "exists": exists,
            "points_examined": len(tuples),
            "points_in_arm": sum(1 for v in verdicts.values() if v["arm"] == arm),
            "verdicts": {
                name: sum(1 for t in tuples if t[0] == name) for name in mitigation_gate.V4_VERDICTS
            },
        }

    capacity_branch, per_sigma = capacity_branches(verdicts, records)

    curve_k, full_k = mitigation_budget.CURVE_K, mitigation_budget.FULL_FIDELITY_K
    promotion = {}
    for key, entry in verdicts.items():
        if entry["verdict"] is None:
            promotion[key] = {"promote": False, "reason": "no verdict: " + entry["reasons"][0]}
            continue
        promote, reason = mitigation_gate.promote_to_full_fidelity(
            verdict=entry["verdict"], reasons=entry["reasons"], curve_k=curve_k, full_k=full_k
        )
        promotion[key] = {"promote": promote, "reason": reason}
    candidates = [key for key, p in promotion.items() if p["promote"]]
    empty = not candidates
    cost16 = _load(_ROOT / "results" / "phase23_cost.json")["sizing"]["16"]

    blob = {
        "governs": (
            "FRONT-04's verdict pass over the 44 committed records, computed AFTER the sweep from "
            "whole-curve inputs (SS-R3), with the promotion rule applied exactly as committed "
            "before any record existed. Every number's source is named; nothing is decided here."
        ),
        "inputs": {
            "point_records": 44,
            "recall_artifact": "results/phase25_recall.json (D-25-18-RECALL)",
            "never_taught_anchors": str(verdict.NEVER_TAUGHT_RECORD.relative_to(_ROOT)),
        },
        "pin_kwargs": list(PIN_KWARGS),
        "pin_sweep_inputs_note": (
            "sweep_extraction_rates and sweep_taught_recalls are recorded AS THE PIN RECEIVED "
            "THEM: the sanctioned route hands it SUPERSEDED_SWEEP_SENTINEL and decides coverage "
            "itself from the four leg-length sequences under whole_curve_inputs (D-34)."
        ),
        "extraction_ceiling": {
            "X": ceiling,
            "tolerated": tolerated,
            "fraction": fraction,
            "tolerance_sentence": sentence,
            "n_questions": 416,
        },
        "point_verdicts": verdicts,
        "legs": legs,
        "leg_refusals": refusals,
        "refused_points": [k for k, v in verdicts.items() if v["verdict"] is None],
        "amended_criterion": (
            "D-25-18-ADV64-REFUSED: 38 of 44 points reach condition (a) and carry the ZERO "
            "TOLERANCE sentence; 6 (the adv_n64 leg) are refused by "
            "phase20_gate_coverage.corrected_point_verdict before the pin because the arm's own "
            "control adv_n64_ratio0p000000 scored held-out recall 0/648, so Y_heldout = 0.7 x 0 = "
            "0 is a criterion any reading clears. Borrowing the DP n=64 control was rejected "
            "under D-16/D-47. Decided by the orchestrator 2026-09-09; reversible in seconds by "
            "re-running this CPU pass. Condition (a) fails on all six adv_n64 points regardless "
            "(3-66 of 416 > X), so no feeding choice could have produced a clear on that leg."
        ),
        "control_readings": reading_sources,
        "floors": floors(),
        "arm_existentials": existentials,
        "arm_existential_counts": existential_counts,
        "capacity_branch": capacity_branch,
        "capacity_per_sigma": per_sigma,
        "adversarial_capacity_rule_absent": verdict.ADVERSARIAL_CAPACITY_RULE_ABSENT,
        "candidates": candidates,
        "empty_frontier_reached": empty,
        "empty_frontier_branch": (
            mitigation_gate._CAPACITY_DISPATCH[(False, False)] if empty else None
        ),
        # A promoted point is redrawn at K=48 (3x the K=16 draws) and replicated once at K=48:
        # 2 readings x 3 x the K=16 ceiling hours per point (results/phase23_cost.json).
        "tail_cost_hours": 0
        if empty
        else len(candidates) * 2 * 3 * cost16["h_per_point_ceiling_at_k"],
        "pre_registered_null": {
            "epsilon_at_sigma_0p5": records["dp_n8_sigma0p500000"]["epsilon"],
            "condition_a": sentence,
            "statement": (
                "epsilon is 519.6981942303134 at sigma=0.5 and condition (a) is ZERO TOLERANCE: "
                "one leaked question of 416 already puts the Wilson upper bound above X"
            ),
        },
        "promotion_rule_verbatim": phase25_prereg.PROMOTION_RULE,
        "promotion_rule_provenance": promotion_rule_provenance(keys),
        "promotion": promotion,
        "ratchet_k": mitigation_gate.ratchet_k(fixed_k=curve_k, proposed_k=full_k),
        "curve_k": curve_k,
        "full_fidelity_k": full_k,
        "gate08_consequence": GATE08_CONSEQUENCE,
        "replication_pending_marker": mitigation_gate.REPLICATION_PENDING_MARKER,
        "replicated_at_second_seed": {
            "value": REPLICATED_AT_SECOND_SEED,
            "source": "every record carries seed 1337 and no replication record exists (D-11)",
        },
        "dp_recall_disclosure": {
            "finding": (
                "Every DP point above sigma=0 scored taught recall 0/1008 and held-out 0/648, "
                "sigma=0.5 (epsilon 519.698) included; only the two sigma=0 controls and the "
                "adversarial arm retain recall. Quoted from results/phase25_recall.json."
            ),
            "taught": {k: v["recall_counts"]["taught"] for k, v in verdicts.items()},
            "heldout": {k: v["recall_counts"]["heldout"] for k, v in verdicts.items()},
        },
        "adversarial_no_replay": ADVERSARIAL_NO_REPLAY,
        "emitted_git_sha": _git("rev-parse", "HEAD"),
    }
    phase25_run.atomic_write_json(RECORD, blob)
    return blob


if __name__ == "__main__":
    b = build()
    print(
        json.dumps(
            {k: b[k] for k in ("arm_existentials", "capacity_branch", "candidates")}, indent=1
        )
    )
    print("verdicts:", sorted({str(v["verdict"]) for v in b["point_verdicts"].values()}))
    print("refusals:", list(b["leg_refusals"]))
