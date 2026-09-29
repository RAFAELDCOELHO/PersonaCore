"""k* extension of Phase 19 — the driver. Committed AFTER `scripts/erasure_kstar_prereg.py`.

It adds NO rule and NO measurement of its own. Every draw comes from the PINNED
`phase19_erasure.run_erasure_arm`; every pooled row from `phase19_run._pooled_rows` (the recovery
from defect C that Phase 19's own target scoring used); every threshold and the k* rule from the
pre-registration. It never calls `erasure_gate.erasure_succeeded` (KSTAR_NO_VERDICT), never calls
`select_ablation_prefix` or `_selected_components` (no re-sweep: the prefix is the COMMITTED
`ordered_prefix`), and never writes to a Phase 19 path.

    python scripts/erasure_kstar_run.py measure 8     # ~70 min on the M3, one process per k
    python scripts/erasure_kstar_run.py measure 16
    python scripts/erasure_kstar_run.py measure 32
    python scripts/erasure_kstar_run.py measure 64
    python scripts/erasure_kstar_run.py summarize     # CPU, seconds; refuses unless all four exist

`measure` refuses unless the rule and this driver are committed and unmodified (KSTAR_INTEGRITY).

A NOTE ON THE `arm` FIELD. Each record is written by `run_erasure_arm("erased", ...)`, so its
`arm` field reads "erased". That is the pin's arm vocabulary, not a claim that this is the M1
record: `erased` is the only arm name that both scores the production adapter under ablation AND
triggers `assert_phase18_parity`. What distinguishes the records is the path
(`results/erasure_kstar_arm_k<NNN>.json`) and `config.ablated_components`, which `summarize` proves
equal to `ordered_prefix[:k]`.
"""

import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import erasure_kstar_prereg as prereg  # noqa: E402
import phase19_erasure as pin  # noqa: E402
import phase19_floor as floor  # noqa: E402
import phase19_run as p19run  # noqa: E402  — for _pooled_rows only (defect C's recovery)

_ROOT = pathlib.Path(__file__).resolve().parent.parent
# The only paths `measure` holds to a clean tree. `results/` is deliberately absent: the records of
# earlier checkpoints are untracked until the run is reviewed, and would otherwise read as dirty.
RULE_PATHSPEC = ("scripts/erasure_kstar_prereg.py", "scripts/erasure_kstar_run.py")
CURVE_PATH = p19run.TARGET_CURVE_PATH  # results/phase19_collateral_curve.json
TARGET_SCORES_PATH = p19run.TARGET_SCORES_PATH  # results/phase19_target_scores.json (k = 78)
SUMMARY_PATH = _ROOT / "results" / "erasure_kstar_summary.json"


def arm_path(k):
    return _ROOT / "results" / f"erasure_kstar_arm_k{k:03d}.json"


def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[erasure_kstar_run] {message}")


def _sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _curve():
    curve = json.loads(CURVE_PATH.read_text(encoding="utf-8"))
    _prove(curve["slot"] == pin.TARGET_SLOT, f"curve slot {curve['slot']!r} != {pin.TARGET_SLOT!r}")
    _prove(
        curve["k"] == prereg.RANK_STOP_K and curve["stopped"] is True,
        f"committed curve reads k = {curve['k']}, stopped = {curve['stopped']}",
    )
    _prove(
        len(curve["ordered_prefix"]) == prereg.RANK_STOP_K,
        f"ordered_prefix holds {len(curve['ordered_prefix'])} addresses, not {prereg.RANK_STOP_K}",
    )
    _prove(
        curve["reference_set_size"] == 8,
        f"curve was read on |R| = {curve['reference_set_size']}, not 8 (defect E's path)",
    )
    return curve


def _curve_agreement(record, curve_row, target_rank_this_run):
    """KSTAR_INTEGRITY's curve-agreement check for one checkpoint. Recorded, never smoothed."""
    tolerance = prereg.CURVE_AGREEMENT_DIALOGUE_TOLERANCE
    run, committed = record["dialogue_ppl"], curve_row["dialogue_ppl"]
    on_diff = abs(run["adapter_on"] - committed["adapter_on"])
    off_diff = abs(run["adapter_off"] - committed["adapter_off"])
    rank_equal = target_rank_this_run == curve_row["target_rank"]
    return {
        "dialogue_on_abs_diff": on_diff,
        "dialogue_off_abs_diff": off_diff,
        "tolerance": tolerance,
        "target_rank_equal": rank_equal,
        "curve_agreement": on_diff <= tolerance and off_diff <= tolerance and rank_equal,
    }


def _provenance(records):
    """Per-checkpoint run provenance; the records must agree on git_sha, torch and device."""
    fields = ("git_sha", "torch", "device")
    per_k = {str(k): {f: r["config"].get(f) for f in fields} for k, r in records.items()}
    for field in fields:
        values = sorted({str(entry[field]) for entry in per_k.values()})
        _prove(len(values) == 1, f"the checkpoint records disagree on config.{field}: {values}")
    sha = next(iter(per_k.values()))["git_sha"]
    _prove(
        sha not in (None, "", "unknown"),
        f"config.git_sha reads {sha!r}: there is no committed tree to hold the run to",
    )
    return per_k


def measure(k):
    _prove(k in prereg.CHECKPOINTS, f"k = {k} is not a pre-registered checkpoint")
    record_path = arm_path(k)
    _prove(not record_path.exists(), f"{record_path} exists — recorded evidence, no force flag")

    from personacore.provenance import refuse_if_dirty

    refuse_if_dirty(
        who="erasure_kstar_run",
        detail=(
            "the k* rule and driver must be committed and unmodified before any measurement "
            "(KSTAR_INTEGRITY)"
        ),
        pathspec=RULE_PATHSPEC,
        cwd=_ROOT,
    )

    import phase14_recall as recall

    from personacore.preflight import preflight_device

    curve = _curve()
    sha_before = _sha256(recall.ADAPTER_PATH)
    _prove(
        sha_before == curve["adapter_in_sha256"],
        f"{recall.ADAPTER_PATH} is not the adapter the committed curve was swept on",
    )
    components = [tuple(address) for address in curve["ordered_prefix"][:k]]
    device = preflight_device(strict=True)["device"]
    print(f"[erasure_kstar_run] k = {k}: ablating the first {len(components)} committed components")
    pin.run_erasure_arm("erased", device, components=components, record_path=record_path)
    _prove(
        _sha256(recall.ADAPTER_PATH) == sha_before,
        f"{recall.ADAPTER_PATH} changed during the run — the production adapter must stay intact",
    )


def _checkpoint_block(k, record, curve, phase18, values):
    config = record["config"]
    _prove(
        [list(a) for a in config["ablated_components"]] == curve["ordered_prefix"][:k],
        f"k = {k}: the record's ablated_components are not ordered_prefix[:{k}]",
    )
    pin.assert_phase18_parity(pin.phase18_parity_config(record))
    family = config["attack_family"]
    budget = config["k"]
    tiers = tuple(sorted({d["tier"] for d in record["draws"] if d["family"] == family}))
    pre = p19run._pooled_rows(phase18["draws"], values, family, tiers)
    post = p19run._pooled_rows(record["draws"], values, family, tiers)
    target_id = pin.target_fact_id(record["draws"])
    target = post[target_id]
    _prove(
        target["n_questions"] == prereg.N_QUESTIONS,
        f"k = {k}: target pooled over {target['n_questions']} questions, not {prereg.N_QUESTIONS}",
    )
    successes = target["n_answerable"]
    deltas = pin.nontarget_deltas(pin.nontarget_rows(pre), pin.nontarget_rows(post))
    by_slot = dict(zip(pin.GATED_NONTARGET_SLOTS, deltas, strict=True))
    margin = pin.MARGIN_K * floor.NONTARGET_NOISE_FLOOR
    rank = {entry["slot"]: entry["rank"] for entry in record["exposure"]}
    curve_row = next(row for row in curve["checkpoints"] if row["prefix"] == k)
    pre_dlg, post_dlg = record["pre_erasure"]["dialogue_ppl"], record["dialogue_ppl"]
    gap_pre = pre_dlg["adapter_on"] - pre_dlg["adapter_off"]
    gap_post = post_dlg["adapter_on"] - post_dlg["adapter_off"]
    curve_gap = curve_row["dialogue_ppl"]["adapter_on"] - curve_row["dialogue_ppl"]["adapter_off"]
    return {
        "k": k,
        "arm_record": record_path_name(k),
        "arm_record_sha256": _sha256(arm_path(k)),
        "attack_family": family,
        "budget_k": budget,
        "tiers_pooled": list(tiers),
        "target": {
            "fact_id": target_id,
            "slot": pin.TARGET_SLOT,
            "successes": successes,
            "n_questions": target["n_questions"],
            "n_draws": target["n_questions"] * budget,
            "per_tier": target["per_tier"],
            "wilson_upper_bound": pin.wilson_upper_bound(successes, target["n_questions"]),
            "rule_of_three": pin.rule_of_three(target["n_questions"]) if successes == 0 else None,
            "clears_target_floor": prereg.clears(successes),
            "exposure_rank_this_run": rank[pin.TARGET_SLOT],
            "exposure_rank_committed_curve": curve_row["target_rank"],
            "value_span_nll_committed_curve": curve_row["target_ans1_mean_nll"],
        },
        "nontarget": {
            r["slot"]: {
                "fact_id": fact_id,
                "pre_answerable": pre[fact_id]["n_answerable"],
                "post_answerable": r["n_answerable"],
                "n_questions": r["n_questions"],
                "delta": by_slot[r["slot"]],
                "over_margin": by_slot[r["slot"]] > margin,
                "exposure_rank_this_run": rank[r["slot"]],
                "value_span_nll_committed_curve": curve_row["slots"][r["slot"]]["ans1_mean_nll"],
            }
            for fact_id, r in sorted(pin.nontarget_rows(post).items())
        },
        "nontarget_margin": margin,
        "nontarget_over_margin_count": sum(d > margin for d in deltas),
        "curve_agreement": _curve_agreement(record, curve_row, rank[pin.TARGET_SLOT]),
        "dialogue": {
            "pre_this_run": pre_dlg,
            "post_this_run": post_dlg,
            "adaptation_destroyed_this_run": 1 - gap_post / gap_pre,
            "post_committed_curve": curve_row["dialogue_ppl"],
            "adaptation_destroyed_committed_curve": 1 - curve_gap / gap_pre,
        },
    }


def record_path_name(k):
    return arm_path(k).name


def summarize():
    _prove(not SUMMARY_PATH.exists(), f"{SUMMARY_PATH} exists — recorded evidence, no force flag")
    missing = [k for k in prereg.CHECKPOINTS if not arm_path(k).exists()]
    _prove(not missing, f"missing checkpoint record(s) {missing}; the rule refuses a subset")

    import phase14_factset as factset

    curve = _curve()
    phase18 = json.loads(pin.PHASE18_ARM_RECORD_PATH.read_text(encoding="utf-8"))
    values = {f.id: f.value for f in factset.LOCKED_FACTS + factset.SOFT_TIER_FACTS}
    records = {k: json.loads(arm_path(k).read_text(encoding="utf-8")) for k in prereg.CHECKPOINTS}
    provenance = _provenance(records)
    blocks = {
        k: _checkpoint_block(k, records[k], curve, phase18, values) for k in prereg.CHECKPOINTS
    }
    decision = prereg.kstar({k: blocks[k]["target"]["successes"] for k in prereg.CHECKPOINTS})
    committed_78 = json.loads(TARGET_SCORES_PATH.read_text(encoding="utf-8"))["target_scores"]
    _prove(
        committed_78["target"]["successes"] == 0
        and committed_78["target"]["n_questions"] == prereg.N_QUESTIONS,
        "the committed k = 78 reading is not 0/27: kstar() takes that 0 for granted",
    )
    kstar_block = blocks.get(decision["kstar"])
    summary = {
        "decision": decision,
        "kstar_block": kstar_block,
        "kstar_block_note": (
            None
            if kstar_block is not None
            else "null case: k* = 78 is Phase 19's committed reading, not re-measured here"
        ),
        "provenance": provenance,
        "curve_agreement_all": all(
            blocks[k]["curve_agreement"]["curve_agreement"] for k in prereg.CHECKPOINTS
        ),
        "integrity": list(prereg.KSTAR_INTEGRITY),
        "checkpoints": {str(k): blocks[k] for k in prereg.CHECKPOINTS},
        "committed_k78_read_not_recomputed": {
            "source": TARGET_SCORES_PATH.name,
            "target_successes": committed_78["target"]["successes"],
            "target_n_questions": committed_78["target"]["n_questions"],
        },
        "rule": list(prereg.KSTAR_RULE),
        "no_verdict": list(prereg.KSTAR_NO_VERDICT),
        "posture": list(prereg.KSTAR_POSTURE),
        "prereg_sha256": _sha256(pathlib.Path(prereg.__file__)),
        "curve_sha256": _sha256(CURVE_PATH),
        "driver": "scripts/erasure_kstar_run.py summarize",
    }
    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=pin.JSON_INDENT, sort_keys=True), encoding="utf-8"
    )
    print(f"[erasure_kstar_run] sequence {decision['sequence']}")
    print(
        f"[erasure_kstar_run] k* = {decision['kstar']}, bracket {decision['bracket']}, "
        f"null_case = {decision['null_case']}, rebound = {decision['rebound_after_kstar']}, "
        f"non_increasing = {decision['non_increasing']}"
    )
    print(
        "[erasure_kstar_run] curve agreement "
        f"{ {k: blocks[k]['curve_agreement']['curve_agreement'] for k in prereg.CHECKPOINTS} }"
    )
    print(f"[erasure_kstar_run] wrote {SUMMARY_PATH}")


def main(argv):
    if len(argv) == 2 and argv[0] == "measure":
        measure(int(argv[1]))
    elif argv == ["summarize"]:
        summarize()
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
