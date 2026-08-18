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

    python scripts/phase19_run.py cal-ablate    # curve + erased adapter  (19-09 task 1)
    python scripts/phase19_run.py cal-score     # the A2/K=48 arm record  (19-09 task 2)

19-10 added three more, for two further things the pin cannot express:

4. THE PIN WRITES NO `results/phase19_noise_floors.json`. `dialogue-floor` writes the two PPL
   READINGS and `noise-floors` writes an arm record; the floors themselves are DERIVED at report
   time by `dialogue_floor_from_record` and `nontarget_noise_floor`, and 19-15's report is the only
   pinned consumer. 19-10 has to publish all three quantities NOW, before 19-11 locks anything, so
   `dialogue-block` / `nontarget-block` / `retention` each derive their block THROUGH the pinned
   functions and merge it into one artifact.

5. THE PINNED (b) PATH CANNOT RUN AS WRITTEN — measured, not inferred. `_nontarget_rates` proves
   `row["n_questions"] == N_TARGET_QUESTIONS` (27, D5's pooled denominator), and BOTH of its
   producers in the pin deliver something else: `target_rows_from_arm_record` scores
   `extraction.GATED_TIER` alone (13 questions/fact) and `run_erasure_arm`'s
   `rows.update(per_fact_rows(...))` loop lets `core_taught` (14) overwrite `core_held_out` (13),
   which is 19-09's published defect C in the (b) position. So `nontarget_deltas` raises SystemExit
   on both sides. `_pooled_rows` below is the recovery 19-09 already used for the calibration rate:
   drive the pin's own `per_fact_rows` ONCE PER TIER and sum, which reconstitutes exactly the
   27 = 14 + 13 the pin demands. The reduction to the gate's scalar is still the pinned
   `nontarget_noise_floor`, never a `max` typed here.

    python scripts/phase19_run.py dialogue-block   # the (c) dialogue floor block  (19-10 task 1)
    python scripts/phase19_run.py nontarget-block  # the (b) per-fact floor block  (19-10 task 2)
    python scripts/phase19_run.py retention        # retention PPL on/off          (19-10 task 3)
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

# 19-10's one artifact, written in three merges (one per task) so each block is committed beside
# the run that measured it. The pin names no such path — see reason 4 in the module docstring.
NOISE_FLOORS_PATH = _REPO_ROOT / "results" / "phase19_noise_floors.json"


def _sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _merge_block(name, block):
    """Merge ONE block into `results/phase19_noise_floors.json`. An existing block is not replaced.

    The refusal is per BLOCK rather than per file, because the three blocks are measured by three
    separate runs an hour apart and the file has to be appendable across them — but a block that
    already exists is recorded evidence with no force flag, exactly like an arm record.
    """
    doc = (
        json.loads(NOISE_FLOORS_PATH.read_text(encoding="utf-8"))
        if NOISE_FLOORS_PATH.exists()
        else {}
    )
    if name in doc:
        raise SystemExit(
            f"[phase19_run] {NOISE_FLOORS_PATH} already carries {name!r} — it is recorded evidence "
            "and there is no force flag. Delete the block in a reviewed commit to re-measure it."
        )
    doc[name] = block
    NOISE_FLOORS_PATH.write_text(
        json.dumps(doc, indent=pin.JSON_INDENT, sort_keys=True), encoding="utf-8"
    )
    print(f"[phase19_run] merged {name!r} into {NOISE_FLOORS_PATH}")


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


def dialogue_block():
    """19-10 task 1 — the (c) dialogue noise floor, DERIVED by the pin from its own record."""
    from personacore.provenance import git_sha

    record = json.loads(pin.DIALOGUE_FLOOR_RECORD_PATH.read_text(encoding="utf-8"))
    # The ONE committed path from that record to the number. It re-proves the pinned seed pair and
    # reads the ON arm, so the floor cannot quietly become an OFF-arm spread (identical across
    # seeds by construction) or one arm's own pre/post difference (the erasure's effect size).
    floor = pin.dialogue_floor_from_record()
    cap = pin.dialogue_cap(floor)
    seed_a, seed_b = pin.DIALOGUE_NOISE_FLOOR_SEEDS
    a = dict(record["dialogue_ppl"][str(seed_a)], seed=seed_a)
    b = dict(record["dialogue_ppl"][str(seed_b)], seed=seed_b)

    # The MASKED published reading — `masked_perplexity` WITH `forbid_ids`, which is what
    # `dialogue_ppl_pair` calls. The teaching log's 5.8176 / 4.5737 pair is the UNMASKED twin
    # (`results/phase14_recall_report.md:465-475`, correction WR-01), quoted here as the second
    # comparison rather than as the target, because `train_arm` has since been aligned to pass
    # `forbid_ids` and this re-teach therefore reports the masked instrument.
    published_on, published_off = (
        pin.V20_TAUGHT_ADAPTER_DIALOGUE_PPL,
        pin.V20_MASKED_DIALOGUE_VAL_PPL,
    )
    twin_on, twin_off = 5.8176, 4.5737
    rel = lambda got, want: abs(got - want) / want * 100.0  # noqa: E731 — one expression, four uses

    block = {
        "estimator": "phase19_erasure.DIALOGUE_NOISE_FLOOR_ESTIMATOR (Q4 option 2, D3)",
        "reduction": "phase19_erasure.dialogue_noise_floor(|dPPL|) via dialogue_floor_from_record",
        "seeds": list(pin.DIALOGUE_NOISE_FLOOR_SEEDS),
        "value": floor,
        "cap": cap,
        "seed_a": a,
        "seed_b": b,
        "adapter_off_identical_across_seeds": a["adapter_off"] == b["adapter_off"],
        "n_targets": a["n_targets"],
        "pre_erasure": {
            "dialogue_ppl_adapter_on": published_on,
            "source": "results/phase14_recall_report.md:462",
            "excess_over_measured_cap": published_on - cap,
            "admitted_by_measured_cap": published_on <= cap,
            "floor_required_to_admit": (published_on - published_off) / pin.MARGIN_K,
        },
        "seed_a_remeasured_vs_published": {
            "measured_adapter_on": a["adapter_on"],
            "published_masked_adapter_on": published_on,
            "abs_delta": abs(a["adapter_on"] - published_on),
            "rel_pct": rel(a["adapter_on"], published_on),
            "measured_adapter_off": a["adapter_off"],
            "published_masked_adapter_off": published_off,
            "adapter_off_abs_delta": abs(a["adapter_off"] - published_off),
            "adapter_off_rel_pct": rel(a["adapter_off"], published_off),
            "wr01_unmasked_twin_adapter_on": twin_on,
            "wr01_unmasked_twin_adapter_off": twin_off,
            "wr01_documented_divergence_on_pct": rel(twin_on, published_on),
            "wr01_documented_divergence_off_pct": rel(twin_off, published_off),
            "plan_tolerance_pct": 0.008,
            "within_plan_tolerance": rel(a["adapter_on"], published_on) <= 0.008,
        },
        "delta_dialog_reference": {
            "value": pin.V20_DIALOGUE_NOISE_FLOOR_FULL_FT,
            "cap": pin.dialogue_cap(pin.V20_DIALOGUE_NOISE_FLOOR_FULL_FT),
            "regime": "FULL FINE-TUNE, Phase 12, LR 9e-05, 1250 steps, seed pair (1337, 2024)",
            "source": "results/finetune_smoke_report.md:49-57",
            "admits_pre_erasure_reading": published_on
            <= pin.dialogue_cap(pin.V20_DIALOGUE_NOISE_FLOOR_FULL_FT),
        },
        "governs": (
            "the MEASURED adapter-regime floor above is what `erasure_succeeded` reads: "
            "`_cmd_report` passes `dialogue_floor_from_record()` as `dialogue_ppl_noise_floor` "
            "(`phase19_erasure.py:3810`). 0.001704 is the full-fine-tune reading published beside "
            "it for the method it supplied, and it does NOT govern any Phase 19 verdict."
        ),
        "record": pin.DIALOGUE_FLOOR_RECORD_PATH.name,
        "record_sha256": _sha256(pin.DIALOGUE_FLOOR_RECORD_PATH),
        "recipe": record["recipe"],
        "git_sha": git_sha(),
        "driver": "scripts/phase19_run.py dialogue-block (UNPINNED)",
    }
    for key in ("value", "cap"):
        print(f"[phase19_run] dialogue {key} = {block[key]!r}")
    print(f"[phase19_run] seed {seed_a} -> {a}\n[phase19_run] seed {seed_b} -> {b}")
    _merge_block("dialogue_ppl_noise_floor", block)


def _pooled_rows(draws, values, family, tiers):
    """Per-fact rows POOLED over both tiers — the 27 = 14 + 13 the pin's own (b) guard demands.

    Reason 5 in the module docstring: `_nontarget_rates` requires `N_TARGET_QUESTIONS`, and neither
    pin producer supplies it. The recovery drives the pin's own `per_fact_rows` once per tier and
    sums, which is 19-09's recovery from defect C applied in the (b) position — the scoring rule
    (`score_records` -> `aggregate_questions`) is still Phase 18's and is never reimplemented here.
    """
    rows = {}
    for tier in tiers:
        for fact_id, row in pin.per_fact_rows(draws, values, family=family, tier=tier).items():
            acc = rows.setdefault(
                fact_id, {"slot": row["slot"], "n_answerable": 0, "n_questions": 0, "per_tier": {}}
            )
            if acc["slot"] != row["slot"] or tier in acc["per_tier"]:
                raise SystemExit(
                    f"[phase19_run] fact {fact_id!r} appears under two slots or twice in tier "
                    f"{tier!r} — the pooled denominator would double-count a question"
                )
            acc["n_answerable"] += row["n_answerable"]
            acc["n_questions"] += row["n_questions"]
            acc["per_tier"][tier] = {
                "n_answerable": row["n_answerable"],
                "n_questions": row["n_questions"],
                "rate": row["rate"],
            }
    for row in rows.values():
        row["rate"] = row["n_answerable"] / row["n_questions"]
    return rows


def nontarget_block():
    """19-10 task 2 — the (b) per-fact noise floor from the committed replicate arm record."""
    import collections

    import phase14_factset as factset

    from personacore.provenance import git_sha

    replicate = pin._load_arm("replicate")
    phase18 = json.loads(pin.PHASE18_ARM_RECORD_PATH.read_text(encoding="utf-8"))
    values = {f.id: f.value for f in factset.LOCKED_FACTS + factset.SOFT_TIER_FACTS}
    family, budget = replicate["config"]["attack_family"], replicate["config"]["k"]
    tiers = tuple(sorted({d["tier"] for d in replicate["draws"] if d["family"] == family}))

    pre = _pooled_rows(phase18["draws"], values, family, tiers)
    post = _pooled_rows(replicate["draws"], values, family, tiers)
    # The pinned pair, on rows that finally satisfy its own denominator guard. `nontarget_rows`
    # drops the target's row (condition (a)'s numerator); `nontarget_deltas` returns a tuple in
    # `GATED_NONTARGET_SLOTS` order; `nontarget_noise_floor` is the ONLY reduction to the scalar.
    deltas = pin.nontarget_deltas(pin.nontarget_rows(pre), pin.nontarget_rows(post))
    floor = pin.nontarget_noise_floor(deltas)
    by_slot = dict(zip(pin.GATED_NONTARGET_SLOTS, deltas, strict=True))

    per_fact = {}
    for fact_id, row in sorted(pin.nontarget_rows(post).items()):
        per_fact[fact_id] = {
            "slot": row["slot"],
            "delta": by_slot[row["slot"]],
            "n_questions": row["n_questions"],
            "pre_answerable": pre[fact_id]["n_answerable"],
            "pre_rate": pre[fact_id]["rate"],
            "pre_per_tier": pre[fact_id]["per_tier"],
            "post_answerable": row["n_answerable"],
            "post_rate": row["rate"],
            "post_per_tier": row["per_tier"],
            "n_draws": row["n_questions"] * budget,
        }

    # THE NON-COLLISION, re-proved over exactly the seed indices this run used rather than argued
    # from the constant. Every question passes through `replicate_seed_stride`, which raises if its
    # Phase 18 window `[i*K, i*K+K)` reaches the offset; a collision would re-read consumed streams
    # and report a floor of exactly zero, so a measured zero and a bug have to be separable.
    indices = sorted({d["seed_index"] for d in replicate["draws"]})
    strides = {i: pin.replicate_seed_stride(i, budget) for i in indices}
    soft_ids = [f.id for f in factset.SOFT_TIER_FACTS]
    census = collections.Counter(d["tier"] for d in replicate["draws"])

    block = {
        "estimator": "phase19_erasure.NONTARGET_NOISE_FLOOR_ESTIMATOR (D4, seed-stride replicate)",
        "reduction": "phase19_erasure.nontarget_noise_floor = max, called (never inlined)",
        "value": floor,
        "margin_at_gate": pin.MARGIN_K * floor,
        "per_fact": per_fact,
        "slot_order": list(pin.GATED_NONTARGET_SLOTS),
        "deltas_in_slot_order": list(deltas),
        "target_slot_excluded": pin.TARGET_SLOT,
        "unit": "question, never the draw",
        "pooled_denominator": pin.N_TARGET_QUESTIONS,
        "tiers_pooled": list(tiers),
        "adapter": "checkpoints/persona_adapter.pt (UNERASED taught adapter)",
        "arm_record": pin.arm_record_path("replicate").name,
        "arm_record_sha256": _sha256(pin.arm_record_path("replicate")),
        "phase18_baseline": pin.PHASE18_ARM_RECORD_PATH.name,
        "attack_family": family,
        "k": budget,
        "n_draws": sum(row["n_draws"] for row in per_fact.values()),
        "seed_stride": {
            "offset": pin.SEED_STRIDE_OFFSET,
            "n_seed_indices": len(indices),
            "max_seed_index": max(indices),
            "phase18_window_end_max": max(indices) * budget + budget,
            "replicate_base_min": min(strides.values()),
            "replicate_base_max": max(strides.values()),
            "collision_free": max(indices) * budget + budget <= pin.SEED_STRIDE_OFFSET,
            "proved_by": "phase19_erasure.replicate_seed_stride, called on every seed index in use",
        },
        "soft_descriptive": {
            "measured": False,
            "slots": list(pin.SOFT_TIER_SLOTS),
            "fact_ids": soft_ids,
            "soft_draws_in_replicate_record": census.get("soft", 0),
            "soft_entries_in_phase18_corpus": 0,
            "tier_census_of_this_arm": dict(census),
            "reason": (
                "results/phase18_corpus.json holds core_taught and core_held_out ONLY — no soft "
                "entry exists for any attack family, so this arm drew no soft question and a soft "
                "rate here would have no draws behind it. SOFT_TIER_DESCRIPTIVE_READ's clause 3 "
                "asks for the POST-erasure soft recall, which is 19-12's arm and not this "
                "pre-erasure replicate; and the substitute read (an exposure rank) is refused by "
                "phase18_extraction.reference_set_for, which _proves the slot is one of the eight "
                "core gated slots. The narrowing is declared here with its census rather than "
                "reported as a measurement that was not taken."
            ),
        },
        "denominator_recovery": (
            "the pinned (b) path raises as written: `_nontarget_rates` demands n_questions == "
            f"{pin.N_TARGET_QUESTIONS} while `target_rows_from_arm_record` delivers 13 (the gated "
            "tier alone) and `run_erasure_arm`'s `rows.update` loop delivers 14 (core_taught "
            "overwriting core_held_out — 19-09's defect C in the (b) position). Both sides above "
            "are pooled from the pin's own `per_fact_rows`, once per tier, which reconstitutes the "
            f"{pin.N_TARGET_QUESTIONS} = 14 + 13 D5 denominator the guard was written for."
        ),
        "parity": {
            "asserted": False,
            "why": (
                "assert_phase18_parity is deliberately NOT for this arm — its own docstring says "
                "so, PARITY_ASSERTED_ARMS is ('erased', 'retrain'), and _cmd_noise_floors' "
                "docstring reads 'the arm parity is NOT asserted'. The stride is offset ON "
                "PURPOSE, so a parity assertion over PARITY_KEYS fails on seed_stride by design."
            ),
            "keys_matching_phase18": [],
            "keys_deliberately_differing": [],
        },
        "git_sha": git_sha(),
        "driver": "scripts/phase19_run.py nontarget-block (UNPINNED)",
    }
    expected = pin.phase18_parity_values()
    for key in pin.PARITY_KEYS:
        side = (
            "keys_matching_phase18"
            if pin._parity_equal(expected[key], replicate["config"][key])
            else "keys_deliberately_differing"
        )
        block["parity"][side].append(key)

    print("[phase19_run] (b) per-fact |drate|, question unit, own denominator, never pooled:")
    for fact_id, row in per_fact.items():
        print(
            f"    {fact_id:<24} {row['slot']:<14} "
            f"{row['pre_answerable']:>2}/{row['n_questions']} -> "
            f"{row['post_answerable']:>2}/{row['n_questions']}   |d| = {row['delta']!r}"
        )
    print(f"    nontarget_noise_floor(max) = {floor!r}; margin at gate = {pin.MARGIN_K * floor!r}")
    _merge_block("nontarget_noise_floor", block)


def retention():
    """19-10 task 3 — retention PPL on a LoRA-ADAPTED model, ON and OFF, in ONE process."""
    import numpy as np
    import phase14_recall as recall
    import phase16_persistence as persistence
    import torch

    from personacore.evaluation.perplexity import retention_perplexity
    from personacore.generation.text import undecodable_ids_mask
    from personacore.lora import adapter_disabled
    from personacore.preflight import preflight_device
    from personacore.provenance import git_sha

    device = preflight_device(strict=True)["device"]
    # `adapter_path=None` is the PRODUCTION taught adapter (`phase14_recall.ADAPTER_PATH`) — the
    # pre-erasure state every Phase 19 comparison is a movement from.
    model, cfg, tok, _forbid, _artifact = recall.load_adapted_model(device, None)
    block_size = pin.ModelConfig.block_size

    on_ppl, on_tokens = retention_perplexity(model, pin.RETENTION_BIN, block_size, device, tok)
    with adapter_disabled(model):
        off_ppl, off_tokens = retention_perplexity(
            model, pin.RETENTION_BIN, block_size, device, tok
        )
    if on_tokens != off_tokens:
        raise SystemExit(f"[phase19_run] on/off denominators differ ({on_tokens} vs {off_tokens})")

    # THE WINDOW ACCOUNTING, checked rather than quoted. `perplexity` slices `data[i : i+block+1]`,
    # so consecutive windows SHARE their boundary token — it is window k's last target and window
    # k+1's context — and every target 1..n-1 is scored exactly once. The denominator is therefore
    # `n - 1`, not the `corpus_len - n_windows` the module docstring's invariant describes (that
    # form assumes disjoint slices). Verified against the committed `results/phase19_arm_cal-erased
    # .json`, whose own retention reading is 1,000,285 = 1,000,286 - 1.
    n_corpus = len(np.memmap(pin.RETENTION_BIN, dtype=np.uint16, mode="r"))
    n_windows = len(range(0, n_corpus - 1, block_size))
    if n_corpus - 1 != on_tokens:
        raise SystemExit(
            f"[phase19_run] window accounting disagrees: {n_corpus} - 1 != {on_tokens} over "
            f"{n_windows} windows at block {block_size}"
        )
    mask = undecodable_ids_mask(tok, cfg.vocab_size)
    cap = pin.V20_EWC_RETENTION_PPL + pin.MARGIN_K * pin.V20_RETENTION_NOISE_FLOOR

    block = {
        "call": f"retention_perplexity(model, RETENTION_BIN, {block_size}, device, tok)",
        "policy": "FROZEN (DEBT-02) — the dead-id mask the generation path applies; the unmasked "
        "v1.0 `perplexity` is not a substitute",
        "adapter": "checkpoints/persona_adapter.pt (UNERASED taught adapter)",
        "adapter_on": on_ppl,
        "adapter_off": off_ppl,
        "delta_on_minus_off": on_ppl - off_ppl,
        "cap": cap,
        "cap_derivation": f"{pin.V20_EWC_RETENTION_PPL} + {pin.MARGIN_K} x "
        f"{pin.V20_RETENTION_NOISE_FLOOR} (scripts/erasure_gate.py:246)",
        "adapter_on_above_cap": on_ppl > cap,
        "adapter_on_headroom": cap - on_ppl,
        "adapter_off_above_cap": off_ppl > cap,
        "bin": str(pin.RETENTION_BIN.relative_to(_REPO_ROOT)),
        "bin_bytes": pin.RETENTION_BIN.stat().st_size,
        "corpus_tokens": n_corpus,
        "n_windows": n_windows,
        "n_scored_tokens": on_tokens,
        "block_size": block_size,
        "dead_id_mask_sha256": persistence.forbid_digest(mask),
        "dead_id_mask_matches_pinned_forbid_ids": persistence.forbid_digest(mask)
        == pin.FORBID_IDS_SHA256,
        "dead_ids_masked": int(mask.sum()),
        "live_ids": int(mask.numel() - mask.sum()),
        "vocab_size": cfg.vocab_size,
        "adapted_precedent": (
            "RETENTION_MEASUREMENT clause 2's PRECEDENT census still holds exactly: "
            "`retention_perplexity` has 6 call sites across 4 modules (finetune_smoke, "
            "finetune_dialog, finetune_ab, build_retention_bin) and none of the four so much as "
            "imports `inject_lora` or `load_adapter`. But clause 2's stronger sentence — "
            "'retention PPL has never once been measured on a LoRA-adapted model in this "
            "repository' — was true when the pin closed and is NO LONGER TRUE, and the caller "
            "that falsified it is "
            "the PIN ITSELF: `run_erasure_arm`'s `_capability()` (phase19_erasure.py:2869) runs on "
            "`load_adapted_model`, so 19-09's calibration arm already recorded "
            "retention_ppl = 3.7583892242829355 over the same 1,000,285 tokens in "
            "results/phase19_arm_cal-erased.json. THE ACCURATE CLAIM FOR THIS BLOCK is therefore "
            "narrower and is stated instead of the stale one: this is the first retention PPL "
            "measured on the PRODUCTION TAUGHT adapter (checkpoints/persona_adapter.pt), and the "
            "first measured ON and OFF in one process and published as a standalone reading with "
            "its own denominator, cap and dead-id mask digest. The pin's prose is CLOSED and was "
            "not edited; the census guard in tests/test_phase19_erasure.py caught the fifth caller "
            "exactly as clause 2 promised it would."
        ),
        "device": str(device),
        "torch": torch.__version__,
        "git_sha": git_sha(),
        "driver": "scripts/phase19_run.py retention (UNPINNED)",
    }
    for key in ("adapter_on", "adapter_off", "cap", "n_windows", "n_scored_tokens"):
        print(f"[phase19_run] retention {key} = {block[key]!r}")
    _merge_block("retention_ppl_pre_erasure", block)


_TABLE = {
    "cal-ablate": cal_ablate,
    "cal-score": cal_score,
    "cal-siblings": cal_siblings,
    "dialogue-block": dialogue_block,
    "nontarget-block": nontarget_block,
    "retention": retention,
}


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in _TABLE:
        raise SystemExit(f"usage: python scripts/phase19_run.py {{{'|'.join(_TABLE)}}}")
    _TABLE[sys.argv[1]]()
