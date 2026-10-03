"""Phase 37 routing module (REPRO-02) — one named function per published Phase 19 defect.

R1a (the committed erased arm) and R1b (the replica arm) both run this module, and Phase 41
imports its defect-E wrapper. It adds NO rule: the verdict is reached only through the CLOSED
pin's `render_verdict`, and every route is the pin's own function fed a corrected input.

The five defects, as published in README and in results/phase19_calibration_correction.md /
results/phase19_reference_set_correction.md:

* A — `zero_result_exposure_gaps` compares key ORDER against records written with `sort_keys=True`,
  so the on-disk record reads `zero_results_have_nll` False and a perfect erasure reads
  INCONCLUSIVE. `route_a` reads the flag off `phase19_run._order_normalised`'s copy.
* B — `_calibration_rate()` reads Phase 18's candidate recall, so the pin's floor is the 0.20
  ceiling branch. `route_b` reads the CORRECTED rate off results/phase19_calibration_correction.json
  and proves the pinned `lock_erasure_floor` gives `phase19_floor.TARGET_FLOOR`.
* C — the committed `per_fact` rows carry one tier's count (14 or 13 of 27), which the pin's (b)
  guard refuses. `route_c` pools both tiers through `phase19_run._pooled_rows`.
* D — the record's `retention_ppl` is the `[ppl, n]` pair and the gate formats a scalar.
  `route_d` passes the scalar; the count travels beside it.
* E — the pin's `erase` path ranks against the calibration twin (|R| = 6 for pet_name) rather than
  `phase18_extraction.reference_set_for` (|R| = 8). `select_target_prefix` is the ERASE-08 wrapper.

`phase19_run.report()` is NEVER called: it rewrites results/phase19_erasure_report.md with no
refusal (research P4). Its A-D routing is reused as its constituent functions instead. This module
never writes a file.
"""

import json
import pathlib
import sys
import types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import phase19_erasure as pin  # noqa: E402
import phase19_floor as floor  # noqa: E402
import phase19_run as p19run  # noqa: E402  — _pooled_rows (C), _order_normalised (A) only
import phase35_prereg  # noqa: E402


def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[phase37_routes] {message}")


def route_a(arm_record):
    """Defect A: the zero-result NLL flag read off the ORDER-NORMALISED record."""
    return pin.zero_results_have_nll(p19run._order_normalised(arm_record))


def route_b():
    """Defect B: the corrected (a) floor, proved through the PINNED `lock_erasure_floor`."""
    correction = json.loads(p19run.CALIBRATION_CORRECTION_PATH.read_text(encoding="utf-8"))
    _prove(
        correction["governs"] == "corrected_target_floor",
        f"the correction record's `governs` field says {correction['governs']!r}, not "
        "'corrected_target_floor'",
    )
    rate = correction["calibration_rate"]
    value = pin.lock_erasure_floor(rate)
    _prove(
        value == floor.TARGET_FLOOR,
        f"lock_erasure_floor({rate!r}) = {value!r} but TARGET_FLOOR is {floor.TARGET_FLOOR!r}",
    )
    return value


def route_c(arm_record, phase18_record):
    """Defect C: (pre, post) per-fact rows pooled over both tiers — 27 questions per core fact."""
    import phase14_factset as factset

    values = {f.id: f.value for f in factset.LOCKED_FACTS + factset.SOFT_TIER_FACTS}
    family = arm_record["config"]["attack_family"]
    tiers = tuple(sorted({d["tier"] for d in arm_record["draws"] if d["family"] == family}))
    return (
        p19run._pooled_rows(phase18_record["draws"], values, family, tiers),
        p19run._pooled_rows(arm_record["draws"], values, family, tiers),
    )


def route_d(arm_record):
    """Defect D: the retention scalar out of the record's `[ppl, n]` pair."""
    pair = arm_record["retention_ppl"]
    _prove(
        isinstance(pair, (list, tuple)) and len(pair) == 2 and isinstance(pair[1], int),
        f"retention_ppl is {pair!r}, not the [ppl, n] pair `retention_perplexity` returns",
    )
    return pair[0]


ROUTES = types.MappingProxyType({"A": route_a, "B": route_b, "C": route_c, "D": route_d})


def rederive(arm_record, *, routes=ROUTES):
    """The Phase 19 verdict on ``arm_record`` through ``routes`` and the ONE pin.render_verdict."""
    phase18 = json.loads(pin.PHASE18_ARM_RECORD_PATH.read_text(encoding="utf-8"))
    pre, post = routes["C"](arm_record, phase18)
    target_id = pin.target_fact_id(arm_record["draws"])
    target_row = post[target_id]
    deltas = pin.nontarget_deltas(pin.nontarget_rows(pre), pin.nontarget_rows(post))
    margin = phase35_prereg.e1_condition_b_margin()
    dialogue_floor = pin.dialogue_floor_from_record()
    _prove(
        dialogue_floor == floor.DIALOGUE_PPL_NOISE_FLOOR,
        f"the dialogue record re-derives {dialogue_floor!r} against the locked "
        f"{floor.DIALOGUE_PPL_NOISE_FLOOR!r}",
    )
    # r1a_rederive's exact expression (phase35_prereg.py): the on-off dialogue gap destroyed.
    g0_block, g1_block = arm_record["pre_erasure"]["dialogue_ppl"], arm_record["dialogue_ppl"]
    g0 = g0_block["adapter_on"] - g0_block["adapter_off"]
    g1 = g1_block["adapter_on"] - g1_block["adapter_off"]
    destroyed = (1 - g1 / g0) * 100
    verdict = pin.render_verdict(
        target_successes=target_row["n_answerable"],
        target_questions=target_row["n_questions"],
        target_floor=routes["B"](),
        nontarget_deltas=deltas,
        nontarget_noise_floor=floor.NONTARGET_NOISE_FLOOR,
        dialogue_ppl=arm_record["dialogue_ppl"]["adapter_on"],
        dialogue_ppl_noise_floor=dialogue_floor,
        retention_ppl=routes["D"](arm_record),
        zero_results_have_nll=routes["A"](arm_record),
    )
    return {
        "k": len(arm_record["config"]["ablated_components"]),
        "target_correct": [target_row["n_answerable"], target_row["n_questions"]],
        "nontargets_beyond_margin": [sum(d > margin for d in deltas), len(deltas)],
        "destroyed_pct": destroyed,
        "margin": margin,
        "target_fact_id": target_id,
        "nontarget_deltas_by_slot": dict(zip(pin.GATED_NONTARGET_SLOTS, deltas, strict=True)),
        "verdict": verdict["verdict"],
        "reasons": list(verdict["reasons"]),
        "gate_inputs": verdict["inputs"],
    }


def b_floor_from_replicate():
    """D-13: the (b) noise floor re-derived from the replicate arm through route_c and the pin."""
    replicate = json.loads(pin.arm_record_path("replicate").read_text(encoding="utf-8"))
    phase18 = json.loads(pin.PHASE18_ARM_RECORD_PATH.read_text(encoding="utf-8"))
    pre, post = route_c(replicate, phase18)
    value = pin.nontarget_noise_floor(
        pin.nontarget_deltas(pin.nontarget_rows(pre), pin.nontarget_rows(post))
    )
    _prove(
        value == floor.NONTARGET_NOISE_FLOOR,
        f"the replicate arm re-derives a (b) floor of {value!r} against the locked "
        f"{floor.NONTARGET_NOISE_FLOOR!r}",
    )
    return value


def select_target_prefix(model, tok, device, artifact, *, fact, dialogue_ppl):
    """Defect E — THE ERASE-08 wrapper (D-08). Phase 41 imports this and writes no other.

    `phase19_run.target_ablate`'s call shape, which produced the committed curve
    (results/phase19_collateral_curve.json, |R| = 8, k = 78): the pin's `select_ablation_prefix`
    ranks against `phase18_extraction.reference_set_for(fact.slot)`, never the calibration twin the
    pin's `_selected_components` would pass. The pin is imported unedited and never monkeypatched;
    neither `reference_set_for_calibration` nor `_selected_components` is called.
    ``dialogue_ppl`` is a zero-argument callable (R1b passes
    ``lambda: pin.dialogue_ppl_pair(model, device, forbid)``).
    """
    import phase14_factset as factset
    import phase18_extraction as extraction

    taught = {f.slot: f.value for f in factset.LOCKED_FACTS}
    return pin.select_ablation_prefix(
        model,
        tok,
        device,
        artifact,
        slot=fact.slot,
        value=fact.value,
        references=extraction.reference_set_for(fact.slot),
        collateral={
            slot: (taught[slot], extraction.reference_set_for(slot))
            for slot in extraction.CORE_SLOTS
        },
        dialogue_ppl=dialogue_ppl,
    )
