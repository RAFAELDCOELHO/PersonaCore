"""UNPINNED THROWAWAY runner for Phase 19 — the two things the CLOSED pin cannot express.

`scripts/phase19_erasure.py` is the pre-registration and is CLOSED at 15 commits: its own `main`
docstring says a run needing something the dispatch table cannot express is "an UNPINNED THROWAWAY
(`python -c ...`, or a new `scripts/phase19_run.py`), never a commit here". This is that file, at
the name that docstring names. It adds NO measurement of its own — every number below comes out of
a committed pin function — and it exists for exactly three reasons, each measured rather than
assumed:

1. `_cmd_cal_erase` DISCARDS the collateral curve. `_selected_components` calls
   `select_ablation_prefix` and returns only `chosen["ordered"][:chosen["k"]]`, printing `k`,
   `cap`, `stopped` and the prefix list to stdout. `ABLATION_STOP_RULE`'s sixth clause calls that
   curve MANDATORY, NOT DIAGNOSTIC — so it has to reach a file, and the pin has no code that
   writes one.

2. `_cmd_cal_erase` NEVER EXPORTS THE ERASED ADAPTER. `run_erasure_arm` applies the ablation with
   `load_adapter_weights(model, ablate_components(artifact, components))` — in memory, on a model
   that exits with the process. T-19-39 requires an `export_adapter` -> `load_adapter_weights`
   round trip with the key + shape + SCALE audits passing on real 331,776-parameter weights, and
   nothing in the pin performs it.

3. `run_erasure_arm` ABORTS on the calibration corpus. It builds
   `values = {f.id: f.value for f in factset.LOCKED_FACTS + factset.SOFT_TIER_FACTS}`
   (`phase19_erasure.py:2814`), which holds the eight candidates and the two soft-tier facts and
   NO member of `CALIBRATION_POOL`. Every draw over the calibration corpus carries
   `fact_id = "cal_person_varek"`, and `phase18_extraction.score_records` `_prove`s
   `record["fact_id"] in values` — "scoring it against nothing would score every draw a miss, and
   a fabricated miss is indistinguishable from a measured one". So `python scripts/phase19_erasure
   .py cal-erase` runs the whole sweep and all 1,104 draws and THEN raises `SystemExit`, having
   written nothing. `cal_score` below supplies the missing value by extending
   `factset.SOFT_TIER_FACTS` for the duration of the one call, which is the narrowest seam that
   exists: it adds the value the scorer needs and touches nothing else the run reads
   (`taught` comes from `LOCKED_FACTS` alone; the Phase 18 rows are scored by fact_id membership,
   never by completeness; `assert_no_value_in_prompt` gets a STRICTLY LONGER forbidden list).

Nothing here re-implements a pin rule. `select_ablation_prefix`, `ablate_components`,
`run_erasure_arm`, `reference_set_for_calibration`, `select_calibration_fact` and
`dialogue_ppl_pair` are all called, never copied.

    python scripts/phase19_run.py cal-ablate    # curve + erased adapter  (task 1)
    python scripts/phase19_run.py cal-score     # the A2/K=48 arm record  (task 2)
"""

import hashlib
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import phase19_erasure as pin  # noqa: E402  — after the path insert, like every phase19 driver

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

# NOT addressed by any pin constant — the pin never writes a curve and never exports an erased
# adapter — so the plan's own two names are used unchanged. The ARM RECORD is the opposite case
# and is NOT named here: it goes wherever `pin.arm_record_path("cal-erased")` says, because
# `_calibration_rate` reads it back through `_load_arm("cal-erased")` and a second name would
# orphan the record from the only function that consumes it.
CURVE_PATH = _REPO_ROOT / "results" / "phase19_calibration_curve.json"
ERASED_ADAPTER_PATH = _REPO_ROOT / "checkpoints" / "phase19_cal_erased_adapter.pt"
SIBLINGS_PATH = _REPO_ROOT / "results" / "phase19_calibration_curve_siblings.json"


def _sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _refuse(path):
    if pathlib.Path(path).exists():
        raise SystemExit(
            f"[phase19_run] {path} already exists — it is recorded evidence and there is no force "
            "flag. Delete it in a reviewed commit if it genuinely must be regenerated."
        )


def cal_ablate():
    """Task 1 — M1 against the calibration adapter: write the curve, export the erased adapter."""
    import phase14_factset as factset
    import phase14_recall as recall
    import phase18_extraction as extraction
    import teach_persona as tp
    import torch

    from personacore.checkpoint import export_adapter, load_adapter
    from personacore.lora import load_adapter_weights
    from personacore.preflight import preflight_device
    from personacore.provenance import git_sha

    _refuse(CURVE_PATH)
    _refuse(ERASED_ADAPTER_PATH)

    fact = pin.select_calibration_fact()
    adapter_path = tp.arm_outputs(pin.CALIBRATION_ARM, prefix=pin.RETRAIN_PREFIX)["adapter"]
    device = preflight_device(strict=True)["device"]
    model, _cfg, tok, forbid, artifact = recall.load_adapted_model(device, adapter_path)

    taught = {f.slot: f.value for f in factset.LOCKED_FACTS}
    references = pin.reference_set_for_calibration(fact.slot, fact)
    collateral = {
        slot: (taught[slot], extraction.reference_set_for(slot)) for slot in extraction.CORE_SLOTS
    }

    started = time.time()
    chosen = pin.select_ablation_prefix(
        model,
        tok,
        device,
        artifact,
        slot=fact.slot,
        value=fact.value,
        references=references,
        collateral=collateral,
        dialogue_ppl=lambda: pin.dialogue_ppl_pair(model, device, forbid),
    )
    wall = time.time() - started
    print(
        f"[phase19_run] M1 stopped at k = {chosen['k']} of {chosen['cap']} "
        f"(stopped = {chosen['stopped']}); curve at {[r['prefix'] for r in chosen['curve']]}"
    )

    selected = list(chosen["ordered"][: chosen["k"]])
    erased = pin.ablate_components(artifact, selected)
    export_adapter(
        ERASED_ADAPTER_PATH,
        adapter=erased["adapter"],
        lora_config=erased["lora_config"],
        base_fingerprint=erased["base_fingerprint"],
    )

    # T-19-39 — the A5 property proved on a toy model at 19-01, re-proved on real weights. The
    # round trip goes through `load_adapter` (weights_only=True) and then through
    # `load_adapter_weights`, which is where the key, shape/dtype and SCALE audits live.
    round_tripped = load_adapter(ERASED_ADAPTER_PATH)
    load_adapter_weights(model, round_tripped)
    audits = {
        "keys_equal": sorted(round_tripped["adapter"]) == sorted(erased["adapter"]),
        "lora_config_equal": round_tripped["lora_config"] == erased["lora_config"],
        "base_fingerprint_equal": round_tripped["base_fingerprint"] == erased["base_fingerprint"],
        "tensors_bit_identical": all(
            torch.equal(round_tripped["adapter"][k].cpu(), v.cpu())
            for k, v in erased["adapter"].items()
        ),
        "n_tensors": len(round_tripped["adapter"]),
        "n_params": sum(int(v.numel()) for v in round_tripped["adapter"].values()),
    }
    # The ablation itself survived the file: every addressed rank-1 component is exactly zero in
    # BOTH factors, read back off disk rather than off the in-memory dict that wrote it.
    zeroed = []
    for layer, projection, j in selected:
        prefix = pin._COMPONENT_PREFIX[(layer, projection)]
        a = round_tripped["adapter"][f"{prefix}.lora_A"][j, :]
        b = round_tripped["adapter"][f"{prefix}.lora_B"][:, j]
        zeroed.append(bool(torch.all(a == 0)) and bool(torch.all(b == 0)))
    audits["ablated_components_zero_on_disk"] = all(zeroed)
    audits["ablated_components_checked"] = len(zeroed)
    for name, value in audits.items():
        print(f"[phase19_run] audit {name}: {value}")
    if not all(audits[k] for k in audits if isinstance(audits[k], bool)):
        raise SystemExit("[phase19_run] the erased adapter failed its round-trip audits — BLOCKER")

    load_adapter_weights(model, artifact)  # leave the model as it was handed over

    record = {
        "fact_id": fact.id,
        "slot": fact.slot,
        "k": chosen["k"],
        "stopped": chosen["stopped"],
        "cap": chosen["cap"],
        "intact_nll": chosen["intact_nll"],
        "checkpoints": list(chosen["curve"]),
        "ordered_prefix": [list(address) for address in selected],
        "references": list(references),
        "collateral_slots": sorted(collateral),
        "mechanism": pin.MECHANISM_ID,
        "adapter_in": str(adapter_path),
        "adapter_in_sha256": _sha256(adapter_path),
        "adapter_out": str(ERASED_ADAPTER_PATH),
        "adapter_out_sha256": _sha256(ERASED_ADAPTER_PATH),
        "round_trip_audits": audits,
        "wall_clock_min": wall / 60,
        "device": str(device),
        "torch": torch.__version__,
        "git_sha": git_sha(),
        "driver": "scripts/phase19_run.py cal-ablate (UNPINNED)",
    }
    CURVE_PATH.write_text(
        json.dumps(record, indent=pin.JSON_INDENT, sort_keys=True), encoding="utf-8"
    )
    print(f"[phase19_run] wrote {CURVE_PATH} in {wall / 60:.1f} min")


def cal_score():
    """Task 2 — score the erased calibration fact at A2/K=48 through the pin's own arm runner."""
    # Imported BEFORE the patch below so every module-level read of the fact set sees the
    # unmodified tuple; the patch then covers exactly one call and nothing else.
    import phase14_factset as factset
    import phase14_recall  # noqa: F401  — module-level fact-set reads happen at import
    import phase18_extraction  # noqa: F401  — same
    import teach_persona as tp

    from personacore.preflight import preflight_device

    curve = json.loads(CURVE_PATH.read_text(encoding="utf-8"))
    components = [tuple(address) for address in curve["ordered_prefix"]]
    fact = pin.select_calibration_fact()
    if curve["fact_id"] != fact.id:
        raise SystemExit(
            f"[phase19_run] the curve was produced for {curve['fact_id']!r} but the pin selects "
            f"{fact.id!r} — the ablation and the scoring would be about different facts"
        )
    adapter_path = tp.arm_outputs(pin.CALIBRATION_ARM, prefix=pin.RETRAIN_PREFIX)["adapter"]

    original = factset.SOFT_TIER_FACTS
    factset.SOFT_TIER_FACTS = original + (fact,)
    print(
        f"[phase19_run] SOFT_TIER_FACTS extended with {fact.id!r} for this call only "
        f"({len(original)} -> {len(factset.SOFT_TIER_FACTS)}); this module's docstring, reason 3"
    )
    try:
        record = pin.run_erasure_arm(
            "cal-erased",
            preflight_device(strict=True)["device"],
            corpus_path=pin.CALIBRATION_CORPUS_PATH,
            adapter_path=adapter_path,
            components=components,
        )
    finally:
        factset.SOFT_TIER_FACTS = original

    rows = record["per_fact"]
    successes = sum(row["n_answerable"] for row in rows.values())
    questions = sum(row["n_questions"] for row in rows.values())
    budget = record["config"]["k"]
    print()
    print("[phase19_run] POST-ERASURE CALIBRATION RATE, in the question unit:")
    for fact_id, row in sorted(rows.items()):
        print(f"    {fact_id:<20} {row['slot']:<14} {row['n_answerable']:>3}/{row['n_questions']}")
    print(f"    TOTAL {successes}/{questions} over {questions * budget} draws at K={budget}")
    print(
        f"    wilson_upper_bound({successes}, {questions}) = "
        f"{pin.wilson_upper_bound(successes, questions)!r}"
    )
    if successes == 0:
        print(f"    rule_of_three({questions}) = {pin.rule_of_three(questions)!r}")
    print(f"    zero_results_have_nll = {pin.zero_results_have_nll(record)}")


def cal_siblings():
    """The collateral read the PIN's own curve cannot give, replayed over the SAME prefixes.

    `_selected_components` builds `collateral` from `{f.slot: f.value for f in LOCKED_FACTS}` —
    the eight CANDIDATE values. On the TARGET adapter (19-10) that is exactly right: `LOCKED_FACTS`
    is what `arm_spec("real")` teaches. On the CALIBRATION adapter it is not, because
    `arm_spec("cal_first_person_replay")` teaches `CALIBRATION_POOL` and NOTHING ELSE, so all eight
    candidate values are UNTAUGHT on this adapter and their ranks measure how an unlearned value
    happens to sit rather than what the ablation cost. `ABLATION_STOP_RULE`'s sixth clause says
    "331,776 parameters carry TEN FACTS" — on this arm those ten are the pool, and this is the read
    that answers whether the mechanism localised.

    The pin's curve is NOT regenerated and NOT replaced. `k` and `ordered` are functions of the
    TARGET's ordering and stopping rule alone, so both files describe the same sweep; the two
    collateral readings publish side by side, in D3's register.
    """
    import phase14_factset as factset
    import phase14_recall as recall
    import torch

    from personacore.lora import load_adapter_weights
    from personacore.preflight import preflight_device
    from personacore.provenance import git_sha

    _refuse(SIBLINGS_PATH)
    curve = json.loads(CURVE_PATH.read_text(encoding="utf-8"))
    ordered = [tuple(address) for address in curve["ordered_prefix"]]
    fact = pin.select_calibration_fact()

    adapter_path = pathlib.Path(curve["adapter_in"])
    if _sha256(adapter_path) != curve["adapter_in_sha256"]:
        raise SystemExit(f"[phase19_run] {adapter_path} is not the file the curve was swept on")
    device = preflight_device(strict=True)["device"]
    model, _cfg, tok, forbid, artifact = recall.load_adapted_model(device, adapter_path)
    del forbid

    pool = {
        f.id: (f, pin.reference_set_for_calibration(f.slot, f)) for f in factset.CALIBRATION_POOL
    }
    started = time.time()
    rows = []
    for prefix in [row["prefix"] for row in curve["checkpoints"]]:
        load_adapter_weights(model, pin.ablate_components(artifact, ordered[:prefix]))
        cells = {}
        for fact_id, (member, refs) in pool.items():
            rank, nll = pin._rank_of(
                model, tok, device, slot=member.slot, value=member.value, references=refs
            )
            cells[fact_id] = {"slot": member.slot, "rank": rank, "ans1_mean_nll": nll}
        rows.append({"prefix": prefix, "facts": cells})
        print(
            f"[phase19_run] prefix {prefix:>3}: "
            + " ".join(
                f"{fid.replace('cal_', '')}={c['rank']}/{c['ans1_mean_nll']:.3f}"
                for fid, c in cells.items()
            )
        )
    load_adapter_weights(model, artifact)

    SIBLINGS_PATH.write_text(
        json.dumps(
            {
                "erased_fact_id": fact.id,
                "erased_slot": fact.slot,
                "k": curve["k"],
                "stopped": curve["stopped"],
                "cap": curve["cap"],
                "pool_order": [f.id for f in factset.CALIBRATION_POOL],
                "reference_set_sizes": {fid: len(refs) for fid, (_f, refs) in pool.items()},
                "checkpoints": rows,
                "curve_companion_to": CURVE_PATH.name,
                "adapter_in": str(adapter_path),
                "adapter_in_sha256": curve["adapter_in_sha256"],
                "wall_clock_min": (time.time() - started) / 60,
                "device": str(device),
                "torch": torch.__version__,
                "git_sha": git_sha(),
                "driver": "scripts/phase19_run.py cal-siblings (UNPINNED)",
            },
            indent=pin.JSON_INDENT,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    print(f"[phase19_run] wrote {SIBLINGS_PATH}")


_TABLE = {"cal-ablate": cal_ablate, "cal-score": cal_score, "cal-siblings": cal_siblings}


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in _TABLE:
        raise SystemExit(f"usage: python scripts/phase19_run.py {{{'|'.join(_TABLE)}}}")
    _TABLE[sys.argv[1]]()
