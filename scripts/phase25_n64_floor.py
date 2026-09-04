"""PLAN 25-15 TASK 2 — D-03: THE n=64 LEG'S OWN MATCHED-CONTROL FLOOR AT THE FULL 5-SEED LADDER.

Runs BEFORE the first sweep point, for two reasons stated rather than assumed:

  1. D-03 itself: the n=64 leg gets its OWN floor from the same estimator that produced
     `MATCHED_CONTROL_NOISE_FLOOR = 0.0267857142857143` at n=8 — `phase23_prereg.noise_floor`,
     CALLED and never inlined — so no floor is borrowed across capacities and there is no capacity
     asymmetry to disclose.
  2. D-50 (measured 2026-09-04 at the launch checkpoint): every point record carries a
     counterfactual retention reading under a v4.0-recipe floor "computed from the sweep's own
     seed-to-seed spread once it exists". The sweep is single-seed per point, so the only
     multi-seed v4.0-recipe adapters in this phase are THESE FIVE. Each seed's adapter is therefore
     also read for `retention_perplexity` (D-45's measurement path, 44 s), and the pairwise
     absolute differences are published here as `retention.seed_spread` — the input
     `phase25_condition_c.counterfactual_retention_floor` takes. No new run: the adapters exist
     for D-03 either way.

THE COMPARATOR IS `phase25_probe2.train_comparator_path` — plan 25-13's seam-off comparator on the
`dp_n64` control's own bins, `phase23_run.train_matched_control`'s body generalised over capacity —
called unchanged at each seed of `phase23_run.SEED_LADDER` with the equalising
`phase23_matched_prereg.MATCHED_GRAD_CLIP`. It trains under the calibration prefix and would
overwrite itself seed to seed, so each adapter is COPIED to a seed-named path under
`checkpoints/` and its sha256 recorded before the next seed releases the calibration targets.

COUNTS WITH DENOMINATORS, NEVER RATES ALONE. Each seed's reading is `(numerator, denominator)` over
the 112 taught questions at 9 draws each (1008), exactly `results/phase23_matched_control.json`'s
`per_seed[].primary`; the reduced floor re-derives from those counts through the called reducer.
"""

import argparse
import datetime
import hashlib
import pathlib
import platform
import shutil
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
_SRC = str(_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import mitigation_budget  # noqa: E402  (scripts/ is not a package)
import phase23_prereg  # noqa: E402  (same)
import phase25_condition_c  # noqa: E402  (same)

RECORD = _ROOT / "results" / "phase25_n64_matched_floor.json"
CAPACITY = "dp_n64"
ESTIMATE_HOURS = 3.3  # D-03: 5 x 23.1 min training + 5 x 16.6 min recall scoring

GOVERNS = (
    "THE TAUGHT RECALL RATE WITH THE ADAPTER ON at n=64 (per_seed[].reading.numerator / "
    ".denominator, a count over QUESTIONS), reduced by the CALLED phase23_prereg.noise_floor — the "
    "same estimator that produced the n=8 floor. It exists so the n=64 leg has its OWN floor: NO "
    "BORROWED FLOOR across capacities, and therefore NO CAPACITY ASYMMETRY TO DISCLOSE (D-03). The "
    "retention block beside it is D-50's input and reduces nothing here."
)


def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[phase25_n64_floor] {message}")


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rel(path):
    return str(pathlib.Path(path).resolve().relative_to(_ROOT))


def retention_seed_spread(retention_by_seed):
    """Pairwise ``|ret_i - ret_j|`` over the seeds, sorted. Non-negative by construction."""
    values = [retention_by_seed[seed] for seed in sorted(retention_by_seed)]
    spread = sorted(
        abs(values[i] - values[j]) for i in range(len(values)) for j in range(i + 1, len(values))
    )
    _prove(spread, "fewer than two seeds — no spread")
    return spread


def kept_adapter(seed):
    return _ROOT / "checkpoints" / f"phase25_n64_floor_seed{seed}_adapter.pt"


def _ensure_bins():
    """The dp_n64 control's bins, built at SEED_LADDER[0] if absent (the comparator's corpus)."""
    import phase14_factset as fs
    import phase23_run as p23
    import phase25_calibrate as cal
    import teach_persona as tp

    facts, second_person, replay_ratio = tp.arm_spec(CAPACITY)
    paths = tp.arm_outputs(CAPACITY, prefix=cal.CALIBRATION_PREFIX)
    targets = [pathlib.Path(t) for t in tp.arm_bin_targets(CAPACITY, paths)]
    if not all(t.exists() for t in targets):
        for target in targets:
            target.unlink(missing_ok=True)
        tp.build_arm_bins(
            CAPACITY,
            facts,
            fs.TAUGHT_FAMILY_IDS,
            second_person=second_person,
            replay_ratio=replay_ratio,
            seed=p23.SEED_LADDER[0],
            prefix=cal.CALIBRATION_PREFIX,
        )
    return {_rel(t): _sha256(t) for t in targets}


def run_seed(seed):
    import phase14_factset as fs
    import phase14_recall as recall
    import phase23_matched_prereg as mp
    import phase25_probe2 as probe2
    import phase25_run
    import teach_persona as tp

    device = phase25_run.device()
    trained = probe2.train_comparator_path(CAPACITY, seed=seed, grad_clip=mp.MATCHED_GRAD_CLIP)
    keep = kept_adapter(seed)
    _prove(not keep.exists(), f"{_rel(keep)} already exists — one attempt per seed")
    shutil.copy2(trained["adapter"], keep)
    digest = _sha256(keep)
    _prove(digest == _sha256(trained["adapter"]), "the kept copy does not hash like the source")

    log_dir = _ROOT / "data" / "phase25_runs" / f"n64_floor_seed{seed}"
    log_dir.mkdir(parents=True, exist_ok=True)
    csv = trained["paths"]["csv"]
    csv_dst = log_dir / "run.csv"
    shutil.move(str(csv), str(csv_dst))

    started = time.time()
    scored = tp.score_arm(trained["arm"], fs.LOCKED_FACTS, keep, device)
    scoring_seconds = time.time() - started

    started = time.time()
    model, _cfg, tok, forbid, _artifact = recall.load_adapted_model(device, keep)
    capability = phase25_condition_c.measure_condition_c(model, tok, device, forbid=forbid)
    del model
    measure_seconds = time.time() - started

    def tier(block):
        return {
            "numerator": int(block["k"]),
            "denominator": int(block["n"]),
            "rate": block["rate"],
            "questions": block["questions"],
            "draws_per_question": 1 + recall.N_SEEDED_SAMPLES,
            "per_family": block["per_family"],
        }

    row = {
        "seed": seed,
        "arm": trained["arm"],
        "reading": tier(scored["on_taught"]),
        "heldout": tier(scored["on_heldout"]),
        "taught_off": tier(scored["off_taught"]),
        "heldout_off": tier(scored["off_heldout"]),
        "adapter": _rel(keep),
        "adapter_sha256": digest,
        "adapter_bytes": keep.stat().st_size,
        "csv": _rel(csv_dst),
        "csv_sha256": _sha256(csv_dst),
        "final_train_loss": trained["final_train_loss"],
        "grad_clip": mp.MATCHED_GRAD_CLIP,
        "clip_calls": trained["clip_calls"],
        "max_pre_clip_norm": trained["max_pre_clip_norm"],
        "training_seconds": trained["seconds"],
        "scoring_seconds": scoring_seconds,
        "measure_seconds": measure_seconds,
        "dialogue": {k: capability[k] for k in ("adapter_on", "adapter_off", "n_targets")},
        "retention": {
            "ppl": capability["retention_ppl"],
            "total_tokens": capability["retention_total_tokens"],
        },
        "git_sha": phase25_run.head_sha(),
    }
    print(
        f"[phase25_n64_floor] seed {seed}: taught {row['reading']['numerator']}/"
        f"{row['reading']['denominator']}, retention {capability['retention_ppl']:.6f}, "
        f"train {trained['seconds']:.0f}s score {scoring_seconds:.0f}s measure "
        f"{measure_seconds:.0f}s",
        flush=True,
    )
    return row


def run(seeds=None):
    import phase23_run as p23
    import phase25_run

    _prove(not RECORD.exists(), f"{_rel(RECORD)} exists — one attempt; delete in a reviewed step")
    seeds = tuple(p23.SEED_LADDER if seeds is None else seeds)
    _prove(
        mitigation_budget.N_CONTROL_SEEDS == len(p23.SEED_LADDER) == len(seeds),
        f"N_CONTROL_SEEDS {mitigation_budget.N_CONTROL_SEEDS} != len(SEED_LADDER) "
        f"{len(p23.SEED_LADDER)} != {len(seeds)}",
    )
    import teach_persona as tp

    n_facts = len(tp.arm_spec(CAPACITY)[0])
    started = time.time()
    bins = _ensure_bins()
    per_seed = [run_seed(seed) for seed in seeds]
    total = time.time() - started

    rates = [row["reading"]["numerator"] / row["reading"]["denominator"] for row in per_seed]
    floor = phase23_prereg.noise_floor(rates)
    retention_by_seed = {str(row["seed"]): row["retention"]["ppl"] for row in per_seed}
    spread = retention_seed_spread(retention_by_seed)

    record = {
        "record": _rel(RECORD),
        "governs": GOVERNS,
        "capacity": CAPACITY,
        "n_facts": n_facts,
        "n_seeds": mitigation_budget.N_CONTROL_SEEDS,
        "seeds": list(seeds),
        "protocol": (
            "phase25_probe2.train_comparator_path: the seam-off comparator on the dp_n64 control's "
            "own bins, phase23_run.train_matched_control generalised over capacity (D-03/D-06); "
            "recall through teach_persona.score_arm over fs.LOCKED_FACTS, adapter ON and OFF"
        ),
        "grad_clip": per_seed[0]["grad_clip"],
        "bins": bins,
        "per_seed": per_seed,
        "floor": floor,
        "floor_call": (
            "phase23_prereg.noise_floor([row['reading']['numerator'] / "
            "row['reading']['denominator'] for row in per_seed])"
        ),
        "estimator": "range: max(readings) - min(readings), committed blind in phase23_prereg",
        "n8_floor_reference": mitigation_budget.MATCHED_CONTROL_NOISE_FLOOR,
        "degenerate_floor_caveat": (
            "a floor of exactly 0.0 records the ABSENCE of spread over a degenerate reading set, "
            "not a measured spread; its consequence is stricter, not looser (Phase 23's "
            "never-taught caveat, restated)"
            if floor == 0.0
            else None
        ),
        "retention": {
            "by_seed": retention_by_seed,
            "seed_spread": spread,
            "spread_rule": (
                "|retention_ppl_i - retention_ppl_j| over every seed pair, sorted ascending; "
                "phase25_condition_c.counterfactual_retention_floor takes the MAX (D-50)"
            ),
            "governs": (
                "D-50's input ONLY: the sweep's own seed-to-seed retention spread under the v4.0 "
                "recipe (fact-aligned n=64 lots, replay at train time, 200 steps, no DP seam). It "
                "reduces nothing in this record and enters no verdict"
            ),
        },
        "cost": {
            "total_seconds": total,
            "estimate_hours": ESTIMATE_HOURS,
            "observed_hours": total / 3600.0,
            "share_of_sweep_envelope": {
                "at_87.86h": total / 3600.0 / 87.86,
                "at_149.45h": total / 3600.0 / 149.45,
            },
        },
        "device": phase25_run.device(),
        "git_sha": phase25_run.head_sha(),
        "python_version": platform.python_version(),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    RECORD.parent.mkdir(parents=True, exist_ok=True)
    phase25_run.atomic_write_json(RECORD, record)
    print(
        f"[phase25_n64_floor] floor {floor!r} (n8 reference "
        f"{mitigation_budget.MATCHED_CONTROL_NOISE_FLOOR!r}), retention spread max "
        f"{max(spread)!r}, {total / 3600.0:.2f} h against {ESTIMATE_HOURS} h -> {_rel(RECORD)}",
        flush=True,
    )
    return record


def main(argv=None):
    import phase25_venue

    print(phase25_venue.launch_banner(), flush=True)
    parser = argparse.ArgumentParser(description="D-03: the n=64 matched-control floor, 5 seeds")
    parser.parse_args(argv)
    run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
