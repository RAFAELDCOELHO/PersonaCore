"""PHASE 36 COST-02 — the v6.0 MPS budget, the stop line, S and the unit caps (D-02..D-19).

A RESOURCE RECORD, NOT AN OUTCOME THRESHOLD. The budget prices every v6.0 MPS front from the five
committed probe records (``results/phase36_probe_*.json``), the committed historical records named
by the Phase 36 pre-registration, and the committed ledger's probe attempts (the probes front, W2).
No verdict reads it.

:func:`derive` is pure arithmetic over records: the HIGH bound of every measured range (D-10, the
pre-registered ``high_bound_rule``), the 25% comparisons (D-02/D-04: a gated divergence refuses
without a written finding), the D-09 unit caps, the D-13 stop line, and when the fronts exceed
Rafael's 90 h ceiling a HALT with the D-15 cut table. No cut is ever applied without Rafael's
ruling.

:func:`dry` prints every number and writes nothing. :func:`emit` writes
``results/phase36_budget.json`` only after the fill file (``scripts/phase36_budget_prereg.py``,
committed after Rafael's approved) exists, re-deriving its values from committed files (the ARCAL
pattern). This module never calls the v6.0 pre-registration's fill: the census allows exactly one
fill site, in a ``phase36_*prereg.py``.

Torch-free at import AND at derive.
"""

import argparse
import datetime
import hashlib
import json
import math
import pathlib
import re
import statistics
import subprocess
import sys
import tempfile

_GIT_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_GIT_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
_SRC = str(_GIT_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import phase25_run  # noqa: E402  (scripts/ is not a package; torch-free)
import phase30_points  # noqa: E402  (same)
import phase35_prereg  # noqa: E402  (same)
import phase36_caps  # noqa: E402  (same)
import phase36_ledger  # noqa: E402  (same)
import phase36_prereg  # noqa: E402  (same)

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402

INSTRUMENT_GIT_SHA = git_sha()

# =================================================================================================
# CONSTANTS — read from the pre-registrations, never typed (the typed proposals carry a source)
# =================================================================================================

BUDGET_RECORD = phase36_caps.BUDGET_RECORD
FILL_FILE = "scripts/phase36_budget_prereg.py"
PROBE_DEVICE = "mps"
CEILING = phase35_prereg.ENTRIES["mps_ceiling_hours"]["value"]

_ENTRIES = phase36_prereg.ENTRIES
STOP_LINE_FACTOR = _ENTRIES["stop_line_factor"]["value"]
MIN_SEEDS = _ENTRIES["cut_table_min_seeds"]["value"]
PROPOSED_SEEDS = _ENTRIES["e2_proposed_seed_count"]["value"]
E3_MAX_STEPS = _ENTRIES["e3_max_steps"]["value"]
E4_POINTS = _ENTRIES["e4_reserve_points"]["value"]
CUT_ORDER = _ENTRIES["cut_order"]["value"]
COMPARATORS = _ENTRIES["divergence_comparators"]["value"]
RULING_ALTERNATIVES = _ENTRIES["high_bound_rule"]["value"]["ruling_alternatives"]
ORDERING_PRICE = _ENTRIES["e1_ordering_price"]["value"]
CALIBRATION_PRICE = _ENTRIES["e1_calibration_price"]["value"]
CANARY_PRICE = _ENTRIES["e4_canary_scoring_price"]["value"]
(_R1B,) = [row for row in COMPARATORS if row["id"] == "r1b_e1_k48"]
ERASED_PRICE = (_R1B["historical_path"], _R1B["historical_key"])

# Typed proposals, each with its requirement as source (CAP_DERIVATIONS).
ORDERINGS = 2  # ERASE-04: the greedy leave-one-out ordering + one alternative
E2_ADAPTERS = 2  # NOISE-01 / Q6: the full taught adapter + M2 without pet_name
RANK02_PREFIXES = (0, 8, 16, 32, 64, 78)  # RANK-02 (and CTX-02's adapters, + M2)
CHECKPOINTS_PER_CELL = 5  # D-09 proposal (ERASE-07 grid), overrulable at the checkpoint
K48_CONFIRMS_PER_CELL = 1  # ERASE-07: the first zero is confirmed once at K = 48
E3_RECIPES = 4  # RECIPE-01: a grid of 4 recipes

CAP_RULING_KEYS = ("E3.max_batch",)
RULING_KEYS = (
    "unit_caps",
    "cuts",
    "divergences_investigated",
    "price_rulings",
    "cap_rulings",
    "approved",
)

HISTORICAL_RECORDS = tuple(
    dict.fromkeys(
        [
            *(
                r["historical_path"]
                for r in COMPARATORS
                if r["probe_field"] and r["historical_path"]
            ),
            ORDERING_PRICE[0],
            CALIBRATION_PRICE["curve"][0],
            CALIBRATION_PRICE["arm"][0],
            CANARY_PRICE[0],
        ]
    )
)

RESOURCE_NOT_OUTCOME = (
    "a RESOURCE record and pre-committed stop line, not an outcome threshold: no verdict reads it"
)

FORMULA = {
    "high_bound": (
        "D-10/D-02 via phase36_prereg high_bound_rule: H1 = max of the repetitions; H2 = a single "
        "draw-loop run priced from its own per-draw distribution (non-draw seconds + questions x "
        "the max per-question block of draw seconds); H3 = the max block mean"
    ),
    "a2_k48_high": "H1: max over the two E1 runs of total_seconds (k = 78, K = 48)",
    "a2_k16_high": "H1: max over the two E1 runs of k16_seconds (fixed + first CURVE_K draws)",
    "a2_question_k48_high": "H1: max over the E1 runs of mean(per_question_k48_seconds)",
    "e1_spread_ratio": "max / min of the two E1 K = 48 run totals",
    "e1_k48_seconds": (
        "E1's per-checkpoint K = 48 price: a2_k48_high by default (a2_draw_basis k78); under the "
        "at_cap ruling max over runs of fixed + questions x K x the MAX at-cap draw seconds"
    ),
    "e1_k16_seconds": "as e1_k48_seconds with k16 for K (a2_draw_basis)",
    "e1_ordering_seconds": (
        "Q5: 60 x results/phase19_collateral_curve.json wall_clock_min, read from the record and "
        "NOT re-measured"
    ),
    "e1_calibration_seconds": (
        "e2_train_m2_high + 60 x results/phase19_calibration_curve.json wall_clock_min + 60 x "
        "results/phase19_arm_cal-erased.json config.wall_clock_min, NOT re-measured (records); "
        "probe_scaled multiplies the two record terms by a2_k48_high / (60 x the erased arm's "
        "wall_clock_min)"
    ),
    "e2_train_m2_high": "H1: max over the two M2 reps of outer_seconds",
    "e2_train_full_high": (
        "the full taught adapter, derived from the M2 probe: max rep loop_seconds (MAX_STEPS "
        "steps, independent of the fact count) + max rep overhead_seconds x n_facts_real / "
        "n_facts_m2"
    ),
    "e2_a2_pass_high": (
        "H2 within_run: a2_pass fixed_seconds + (draws / draws_per_question) x max per-question "
        "block sum; spread_scaled: a2_pass total_seconds x e1_spread_ratio"
    ),
    "e3_per_step_high": (
        "H1: max over the T = STEP_BUDGET and T = e3_max_steps runs of loop_seconds / steps; "
        "x max_batch / the probed batch when Rafael's cap ruling raises E3.max_batch (linear in "
        "batch, a high bound; E4 keeps the v4.0 batch)"
    ),
    "e3_overhead_high": "H1: max over the two E3 runs of overhead_seconds",
    "e3_score_high": (
        "H2 within_run on the T = STEP_BUDGET score_arm pass (score does not depend on T); "
        "spread_scaled: score_seconds x e1_spread_ratio"
    ),
    "e4_canary_seconds": (
        "D-19: results/phase26_canary_sources.json points.<E3 probe point>.provenance."
        "scoring_seconds, used as the high bound and NOT re-measured"
    ),
    "e4_point_seconds": (
        "D-06/D-19: e3_overhead_high + STEP_BUDGET x e3_per_step_high (unscaled: E4 audits the "
        "v4.0 recipe) + e4_canary_seconds; carried in unit_prices for Phase 43's first-point check"
    ),
    "e5_prices": (
        "H3: clearance setup_seconds; max per_slot_seconds; match spread max; max over adapters "
        "and slots of per_slot_mean_candidate_seconds; max candidates_per_slot"
    ),
    "adapter_setup_high": "max of the E5 scoring adapter setups and the E6 setup",
    "e6_anchor_draw_high": "H3: max of per_slot_draw_seconds_mean",
    "probes": (
        "W2 / D-11 / D-12: phase36_ledger.spent(tracked, ledger_path=<the committed ledger blob>, "
        "fronts=('probes',))['by_front']['probes'] — the five records' provenance.run clocks PLUS "
        "every lost probe attempt, never the five records alone"
    ),
    "R1b": (
        "D-04: one erased-arm reading = a2_k48_high (the measured k = 78 reading under every "
        "ruling). Other Phase 19 arms (retrain 46.6 min, replicate 45.3 min) and the M1 re-sweep "
        "(6.959 min) are NOT in R1b's hours: if Phase 37 wants them they need Rafael's approved "
        "(D-06: nothing reallocated)"
    ),
    "E1": (
        "cells x (e1_ordering_seconds + checkpoints_per_cell x e1_k16_seconds + "
        "k48_confirms_per_cell x e1_k48_seconds) + calibrations x e1_calibration_seconds"
    ),
    "E2": (
        "Q6: seeds x (e2_train_m2_high + e2_train_full_high + adapters x e2_a2_pass_high), the "
        "full 2 adapters x S retrain set; Phase 40 reusing existing seed adapters is savings, "
        "not a cut"
    ),
    "E3": (
        "recipes x sigmas x (e3_overhead_high + max_steps x e3_per_step_high + e3_score_high); "
        "the reused v4.0 sigma = 0 cell is not discounted (a high bound)"
    ),
    "E4": "points x e4_point_seconds (D-06: up to e4_reserve_points; never reallocated)",
    "E5": (
        "e5_clearance_setup + sets x e5_slot_clearance_high + sets x max_set_size x e5_match_high "
        "+ prefixes x (adapter_setup_high + sets x max_set_size x e5_nll_high)"
    ),
    "E6": (
        "adapters x (adapter_setup_high + entries x a2_question_k48_high x max_k / "
        "FULL_FIDELITY_K + (entries + anchor_slots) x e5_candidates_per_slot_max x e5_nll_high) + "
        "anchor_adapters x anchor_slots x max_k x e6_anchor_draw_high. The A2-context generation "
        "is priced in full at entries x max_k; reusing the committed K = 48 A2 records for k in "
        "{8,16,32,64,78} and M2 is Phase 39's call and would be savings"
    ),
    "hours": "front_hours = seconds / 3600 per V6_MPS_FRONTS, unrounded; total = math.fsum",
    "stop_line": "D-13: min(stop_line_factor x total, mps_ceiling_hours), only when total fits",
    "halt": (
        "D-15 / COST-02: total above mps_ceiling_hours -> HALT and the cut table in cut_order; "
        "no row is applied without Rafael's ruling; S below cut_table_min_seeds is never a row"
    ),
}

CAP_DERIVATIONS = {
    "E1.cells": "e1_targets x ORDERINGS (2, ERASE-04) x e1_teaching_seeds, read from the E1 record",
    "E1.checkpoints_per_cell": "5: the D-09 proposal for the ERASE-07 grid",
    "E1.k48_confirms_per_cell": "1: ERASE-07 confirms the first zero once at K = 48",
    "E1.calibrations": "ORDERINGS x e1_teaching_seeds (ERASE-06 per ordering and seed)",
    "E2.adapters": "2: the full taught adapter and M2 (NOISE-01, Q6)",
    "E2.seeds": "phase36_prereg e2_proposed_seed_count (D-14)",
    "E3.recipes": "4: RECIPE-01's grid of 4 recipes",
    "E3.sigmas": "len(E3_SIGMAS) of the v6.0 pre-registration",
    "E3.max_steps": "phase36_prereg e3_max_steps (D-05)",
    "E3.max_batch": "the E3 probe record's configuration batch (W10: a ruling may raise it)",
    "E4.points": "phase36_prereg e4_reserve_points (D-06)",
    "E5.sets": "the E5 probe record's configuration slots",
    "E5.max_set_size": "the v6.0 pre-registration's e5_max_set_size",
    "E5.prefixes": "len(RANK02_PREFIXES) = 6 (RANK-02: k = 0, 8, 16, 32, 64, 78)",
    "E6.adapters": "len(RANK02_PREFIXES) + 1 = 7 (CTX-02: the six prefixes and M2)",
    "E6.anchor_adapters": "the same 7 adapters (CTX-02)",
    "E6.anchor_slots": "the E6 probe record's configuration anchor_slots",
    "E6.entries": "the E1 probe record's configuration questions (the A2 corpus, CTX-01)",
    "E6.max_k": "FULL_FIDELITY_K",
}

SURFACED = (
    "Q3: the ledger is committed at ledger/v6_mps_ledger.jsonl; raw beats stay in gitignored data/",
    "Q4: the fill file and results/phase36_budget.json are committed only after Rafael's approved",
    "Q5: each E1 cell's ordering is priced from phase19_collateral_curve wall_clock_min, not "
    "re-measured",
    "Q6: E2 is priced as the full 2 adapters x S retrain set; reuse by Phase 40 is savings",
    "E1 calibration: priced from the calibration curve + cal-erased records + the E2 training unit "
    "(default records; alternative probe_scaled)",
    "E5 clearance premise: one cached probe pass per slot prices each minted set's clearance",
    "E6: the A2-context generation is priced in full at entries x max_k",
    "R1b scope: one erased-arm reading; retrain / replicate arms or the M1 re-sweep need Rafael's "
    "approved",
    "E2 full adapter: MAX_STEPS loop like M2 + M2's overhead x n_facts_real / n_facts_m2",
    "probes front: read from the committed ledger, lost attempts included (W2)",
    "W6: the proposed E3 recipes cap of 4 is counted by phase36_caps.counts_for over ALL cells of "
    "e3_grid_subset, so a reused sigma = 0 cell's recipe counts; Rafael rules recipes 4 (a "
    "5-recipe grid then needs a new budget) or 5 (E3 hours at recipes 5 are printed beside 4)",
    "E3 max_batch = the probed batch; a larger batch needs Rafael's cap ruling (W10)",
)

CUT_QUESTIONS = {
    "e4_reserve": "AUDIT-01..03: the one-run audit of v4.0's epsilon claims",
    "e6_anchor_adapters": "CTX-02: anchor-context generation on the dropped adapters",
    "e2_seeds_to_3": "NOISE-01/02: the precision of the seed noise floor",
    "e3_whole": (
        "RECIPE-01..04: whether any DP recipe keeps recall at large epsilon; E3 at 0 h also "
        "blocks Phase 42's e3_grid_subset by construction"
    ),
    "e1_checkpoints": "ERASE-07: the resolution of the checkpoint grid",
    "r1b": "REPRO-03: the MPS replica of k = 78 beside the Phase 19 verdict",
    "e1_core": (
        "ERASE-03..10: whether erasure generalises across the four targets x two orderings x two "
        "seeds; E1 at 0 h also blocks Phase 41's e1_checkpoint_grid (its fill refuses E1 <= 0)"
    ),
}


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase36_budget] {message}")


_prove(set(CUT_QUESTIONS) == set(CUT_ORDER), "CUT_QUESTIONS does not cover cut_order")


def _is_count(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _at(blob, key):
    """Walk a key path; ``"*"`` fans out over a list and returns the list of leaves."""
    for i, part in enumerate(key):
        if part == "*":
            return [_at(item, key[i + 1 :]) for item in blob]
        blob = blob[part]
    return blob


# =================================================================================================
# THE 25% COMPARISONS (D-02 / D-04), mechanical from divergence_comparators
# =================================================================================================


def _historical_seconds(row, historical):
    blob = historical[row["historical_path"]]
    key = row["historical_key"]
    if isinstance(key, str):  # a regex over a markdown report
        match = re.search(key, blob)
        _prove(match, f"{row['historical_path']} has no match for {key!r}")
        value = float(match.group(1))
    else:
        value = _at(blob, key)
        value = max(value) if isinstance(value, list) else value
    return value * 60 if row["unit"] == "min" else value


def comparisons(probes, historical):
    """One row per divergence_comparators entry with a probe_field (r1b_e1_k48: one per E1 run)."""
    rows = []
    for row in COMPARATORS:
        if row["probe_field"] is None:  # e1_phase31_beside: never compared nor extrapolated
            continue
        stages = probes[row["front"].lower()]["stages"]
        if row["id"] == "e3_t800_linearity":
            longest, short = stages["t_max_steps"], stages["t_step_budget"]
            scaled = longest["steps"] / short["steps"] * short["loop_seconds"]
            pairs = [(longest["loop_seconds"], scaled)]
        else:
            if row["id"] == "e2_training_context":
                probe = [max(r["outer_seconds"] for r in stages["train_reps"])]
            else:
                probe = _at(stages, row["probe_field"].replace("[*]", ".*").split("."))
                probe = probe if isinstance(probe, list) else [probe]
            history = _historical_seconds(row, historical)
            pairs = [(p, history) for p in probe]
        for i, (p, h) in enumerate(pairs, start=1):
            rows.append(
                {
                    "id": row["id"] + (f"#{i}" if len(pairs) > 1 else ""),
                    "gated": row["gated"],
                    "probe_seconds": p,
                    "historical_seconds": h,
                    "divergence": phase36_prereg.divergence(p, h),
                    "exceeds": phase36_prereg.exceeds(p, h),
                }
            )
    return rows


# =================================================================================================
# UNIT PRICES (seconds, unrounded) AND THEIR RULING ALTERNATIVES (W5 / W6)
# =================================================================================================


def _h2(fixed, draws, per_question, draw_seconds):
    """H2: non-draw seconds + questions x the max per-question block of draw seconds."""
    _prove(
        len(draw_seconds) == draws and draws and draws % per_question == 0,
        f"{len(draw_seconds)} draw seconds for {draws} draws at {per_question} per question",
    )
    blocks = [draw_seconds[i : i + per_question] for i in range(0, draws, per_question)]
    return fixed + (draws / per_question) * max(math.fsum(b) for b in blocks)


def unit_prices(probes, historical):
    """Every unit price in seconds, by the pre-registered high-bound rules (D-10)."""
    e1, e2, e3 = (probes[f]["stages"] for f in ("e1", "e2", "e3"))
    e5, e6 = probes["e5"]["stages"], probes["e6"]["stages"]
    runs = e1["runs"]
    totals = [r["total_seconds"] for r in runs]
    reps = e2["train_reps"]
    c2 = probes["e2"]["configuration"]
    a2 = e2["a2_pass"]
    e3_runs = (e3["t_step_budget"], e3["t_max_steps"])
    score = e3["t_step_budget"]
    adapters = e5["scoring"]["adapters"]
    a2_question = max(statistics.fmean(r["per_question_k48_seconds"]) for r in runs)
    beside = probes["e6"]["a2_context_from_e1"]["a2_context_question_k48_seconds_high"]
    _prove(
        beside == a2_question,
        f"the E6 record's A2-context unit {beside} is not the E1 record's {a2_question}: E6 was "
        "emitted beside a different E1 run",
    )
    m2 = max(r["outer_seconds"] for r in reps)
    prices = {
        "a2_k48_high": max(totals),
        "a2_k16_high": max(r["k16_seconds"] for r in runs),
        "a2_question_k48_high": a2_question,
        "e1_spread_ratio": max(totals) / min(totals),
        "e1_ordering_seconds": 60 * _at(historical[ORDERING_PRICE[0]], ORDERING_PRICE[1]),
        "e2_train_m2_high": m2,
        "e2_train_full_high": max(r["loop_seconds"] for r in reps)
        + max(r["overhead_seconds"] for r in reps) * c2["n_facts_real"] / c2["n_facts_m2"],
        "e1_calibration_seconds": m2
        + 60 * _at(historical[CALIBRATION_PRICE["curve"][0]], CALIBRATION_PRICE["curve"][1])
        + 60 * _at(historical[CALIBRATION_PRICE["arm"][0]], CALIBRATION_PRICE["arm"][1]),
        "e2_a2_pass_high": _h2(
            a2["fixed_seconds"], a2["draws"], a2["draws_per_question"], a2["draw_seconds"]
        ),
        "e3_per_step_high": max(r["loop_seconds"] / r["steps"] for r in e3_runs),
        "e3_overhead_high": max(r["overhead_seconds"] for r in e3_runs),
        "e3_score_high": _h2(
            score["score_fixed_seconds"],
            score["score_draws"],
            score["score_draws_per_question"],
            score["score_draw_seconds"],
        ),
        "e4_canary_seconds": _at(historical[CANARY_PRICE[0]], CANARY_PRICE[1]),
        "e5_clearance_setup": e5["clearance"]["setup_seconds"],
        "e5_slot_clearance_high": max(e5["clearance"]["per_slot_seconds"]),
        "e5_match_high": e5["clearance"]["match_seconds_spread"]["max"],
        "e5_nll_high": max(s for a in adapters for s in a["per_slot_mean_candidate_seconds"]),
        "e5_candidates_per_slot_max": max(n for a in adapters for n in a["candidates_per_slot"]),
        "adapter_setup_high": max([a["setup_seconds"] for a in adapters] + [e6["setup_seconds"]]),
        "e6_anchor_draw_high": max(e6["per_slot_draw_seconds_mean"]),
    }
    prices["e1_k48_seconds"] = prices["a2_k48_high"]  # a2_draw_basis k78 (the default)
    prices["e1_k16_seconds"] = prices["a2_k16_high"]
    prices["e4_point_seconds"] = (
        prices["e3_overhead_high"]
        + phase35_prereg.STEP_BUDGET * prices["e3_per_step_high"]
        + prices["e4_canary_seconds"]
    )
    for name, value in prices.items():
        _prove(
            isinstance(value, (int, float)) and math.isfinite(value) and value >= 0,
            f"price {name} = {value!r} is not a finite number >= 0",
        )
    return prices


def price_alternatives(probes, historical):
    """``{ruling name: {alternative: the prices it replaces, or None when unavailable}}``."""
    prices = unit_prices(probes, historical)
    runs = probes["e1"]["stages"]["runs"]
    c1 = probes["e1"]["configuration"]
    maxima = [r["at_cap_seconds_spread"]["max"] for r in runs if r["at_cap_seconds_spread"]]
    high = max(maxima) if maxima else None  # W3: D-10's HIGH bound, never the median
    at_cap = None
    if high is not None:
        at_cap = {
            "e1_k48_seconds": max(
                r["fixed_seconds"] + c1["questions"] * c1["K"] * high for r in runs
            ),
            "e1_k16_seconds": max(
                r["fixed_seconds"] + c1["questions"] * c1["k16"] * high for r in runs
            ),
        }
    e2, e3 = probes["e2"]["stages"], probes["e3"]["stages"]
    ratio = prices["e1_spread_ratio"]
    record_minutes = _at(
        historical[CALIBRATION_PRICE["curve"][0]], CALIBRATION_PRICE["curve"][1]
    ) + _at(historical[CALIBRATION_PRICE["arm"][0]], CALIBRATION_PRICE["arm"][1])
    erased_seconds = 60 * _at(historical[ERASED_PRICE[0]], ERASED_PRICE[1])
    return {
        "a2_draw_basis": {"at_cap": at_cap},
        "single_run_draw_loop": {
            "spread_scaled": {
                "e2_a2_pass_high": e2["a2_pass"]["total_seconds"] * ratio,
                "e3_score_high": e3["t_step_budget"]["score_seconds"] * ratio,
            }
        },
        "e1_calibration": {
            "probe_scaled": {
                "e1_calibration_seconds": prices["e2_train_m2_high"]
                + 60 * record_minutes * (prices["a2_k48_high"] / erased_seconds)
            }
        },
    }


def apply_price_rulings(prices, alternatives, price_rulings):
    """Swap in each ruled alternative; keys and values validated against ruling_alternatives."""
    out = dict(prices)
    for name, choice in price_rulings.items():
        _prove(
            name in RULING_ALTERNATIVES,
            f"price ruling {name!r} is not one of {tuple(RULING_ALTERNATIVES)}",
        )
        default, alternative = RULING_ALTERNATIVES[name]
        _prove(
            choice in (default, alternative),
            f"price ruling {name} = {choice!r} is neither {default!r} nor {alternative!r}",
        )
        if choice == default:
            continue
        swap = alternatives[name][alternative]
        _prove(
            swap is not None,
            f"price ruling {name} = {choice!r} is unavailable: no at-cap draw in either E1 run",
        )
        _prove(
            set(swap) <= set(out), f"{name} replaces unknown prices {sorted(set(swap) - set(out))}"
        )
        out.update(swap)
    return out


# =================================================================================================
# CAPS (D-09), FRONT HOURS, THE CUT TABLE (D-15) AND derive
# =================================================================================================


def proposed_unit_caps(probes):
    """The D-09 proposal, one per phase36_caps.CAP_FIELDS name (CAP_DERIVATIONS states each)."""
    c1 = probes["e1"]["configuration"]
    adapters = len(RANK02_PREFIXES) + 1
    return {
        "E1": {
            "cells": c1["e1_targets"] * ORDERINGS * c1["e1_teaching_seeds"],
            "checkpoints_per_cell": CHECKPOINTS_PER_CELL,
            "k48_confirms_per_cell": K48_CONFIRMS_PER_CELL,
            "calibrations": ORDERINGS * c1["e1_teaching_seeds"],
        },
        "E2": {"adapters": E2_ADAPTERS, "seeds": PROPOSED_SEEDS},
        "E3": {
            "recipes": E3_RECIPES,
            "sigmas": len(phase35_prereg.E3_SIGMAS),
            "max_steps": E3_MAX_STEPS,
            "max_batch": probes["e3"]["configuration"]["batch"],
        },
        "E4": {"points": E4_POINTS},
        "E5": {
            "sets": probes["e5"]["configuration"]["slots"],
            "max_set_size": phase35_prereg.ENTRIES["e5_max_set_size"]["value"],
            "prefixes": len(RANK02_PREFIXES),
        },
        "E6": {
            "adapters": adapters,
            "anchor_adapters": adapters,
            "anchor_slots": probes["e6"]["configuration"]["anchor_slots"],
            "entries": c1["questions"],
            "max_k": phase35_prereg.FULL_FIDELITY_K,
        },
    }


def _front_seconds(p, caps, r1b_cut):
    """Seconds per V6_MPS_FRONTS front except probes (the FORMULA entries, verbatim)."""
    e1, e2, e3, e5, e6 = (caps[f] for f in ("E1", "E2", "E3", "E5", "E6"))
    full_k = phase35_prereg.FULL_FIDELITY_K
    return {
        "R1b": 0.0 if r1b_cut else p["a2_k48_high"],
        "E1": e1["cells"]
        * (
            p["e1_ordering_seconds"]
            + e1["checkpoints_per_cell"] * p["e1_k16_seconds"]
            + e1["k48_confirms_per_cell"] * p["e1_k48_seconds"]
        )
        + e1["calibrations"] * p["e1_calibration_seconds"],
        "E2": e2["seeds"]
        * (p["e2_train_m2_high"] + p["e2_train_full_high"] + e2["adapters"] * p["e2_a2_pass_high"]),
        "E3": e3["recipes"]
        * e3["sigmas"]
        * (p["e3_overhead_high"] + e3["max_steps"] * p["e3_per_step_high"] + p["e3_score_high"]),
        "E4": caps["E4"]["points"] * p["e4_point_seconds"],
        "E5": p["e5_clearance_setup"]
        + e5["sets"] * p["e5_slot_clearance_high"]
        + e5["sets"] * e5["max_set_size"] * p["e5_match_high"]
        + e5["prefixes"]
        * (p["adapter_setup_high"] + e5["sets"] * e5["max_set_size"] * p["e5_nll_high"]),
        "E6": e6["adapters"]
        * (
            p["adapter_setup_high"]
            + e6["entries"] * p["a2_question_k48_high"] * e6["max_k"] / full_k
            + (e6["entries"] + e6["anchor_slots"])
            * p["e5_candidates_per_slot_max"]
            * p["e5_nll_high"]
        )
        + e6["anchor_adapters"] * e6["anchor_slots"] * e6["max_k"] * p["e6_anchor_draw_high"],
    }


def cut_table(prices, caps, front_hours, total):
    """D-15: every row in cut_order with its hours and its lost question; NEVER applies one."""
    e1, e2, e6 = caps["E1"], caps["E2"], caps["E6"]
    per_seed = (
        prices["e2_train_m2_high"]
        + prices["e2_train_full_high"]
        + e2["adapters"] * prices["e2_a2_pass_high"]
    )
    checkpoint_units = e1["checkpoints_per_cell"] - 1 if e1["cells"] else 0
    checkpoint_hours = e1["cells"] * prices["e1_k16_seconds"] / 3600
    rows = {
        "e4_reserve": ("the E4 reserve whole", front_hours["E4"], int(caps["E4"]["points"] > 0)),
        "e6_anchor_adapters": (
            "one adapter's anchor generation",
            e6["anchor_slots"] * e6["max_k"] * prices["e6_anchor_draw_high"] / 3600,
            e6["anchor_adapters"],
        ),
        "e2_seeds_to_3": (
            f"S from {e2['seeds']} to {MIN_SEEDS} (never below, D-14)",
            (e2["seeds"] - MIN_SEEDS) * per_seed / 3600,
            int(e2["seeds"] > MIN_SEEDS),
        ),
        "e3_whole": ("the E3 front whole", front_hours["E3"], int(caps["E3"]["recipes"] > 0)),
        "e1_checkpoints": ("one checkpoint per cell", checkpoint_hours, checkpoint_units),
        "r1b": ("the R1b reading", front_hours["R1b"], int(front_hours["R1b"] > 0)),
        "e1_core": (
            "the E1 front whole (after the e1_checkpoints row's units)",
            front_hours["E1"] - checkpoint_units * checkpoint_hours,
            int(e1["cells"] > 0 or e1["calibrations"] > 0),
        ),
    }
    table = []
    for cut in CUT_ORDER:
        unit, hours, units = rows[cut]
        if units:
            table.append(
                {
                    "id": cut,
                    "unit": unit,
                    "hours_per_unit": hours,
                    "max_units": units,
                    "hours_saved_max": hours * units,
                    "question_lost": CUT_QUESTIONS[cut],
                }
            )
    return table


def _prove_caps(caps, cap_rulings, probed_batch):
    fields = phase36_caps.CAP_FIELDS
    _prove(
        isinstance(caps, dict) and set(caps) == set(fields),
        f"unit_caps must be keyed by exactly {sorted(fields)}",
    )
    for front, names in fields.items():
        _prove(
            isinstance(caps[front], dict) and set(caps[front]) == set(names),
            f"unit_caps[{front!r}] must carry exactly {names}",
        )
        for name, value in caps[front].items():
            _prove(
                _is_count(value), f"unit_caps[{front!r}][{name!r}] = {value!r} is not an int >= 0"
            )
    _prove(
        caps["E2"]["seeds"] >= MIN_SEEDS,
        f"E2 seeds {caps['E2']['seeds']} is below cut_table_min_seeds {MIN_SEEDS} (D-14): never "
        "without asking Rafael",
    )
    _prove(caps["E2"]["adapters"] == E2_ADAPTERS, f"E2 adapters must be {E2_ADAPTERS} (Q6)")
    _prove(
        caps["E3"]["max_steps"] <= E3_MAX_STEPS,
        f"E3 max_steps {caps['E3']['max_steps']} is above e3_max_steps {E3_MAX_STEPS} (D-05)",
    )
    for key, text in cap_rulings.items():
        _prove(key in CAP_RULING_KEYS, f"cap ruling {key!r} is not one of {CAP_RULING_KEYS}")
        _prove(isinstance(text, str) and text.strip(), f"cap ruling {key} is empty")
    _prove(
        caps["E3"]["max_batch"] <= probed_batch or "E3.max_batch" in cap_rulings,
        f"E3 max_batch {caps['E3']['max_batch']} is above the probed batch {probed_batch}: only "
        "Rafael's cap ruling (cap_rulings['E3.max_batch']) raises it (W10)",
    )


def _apply_cuts(caps, cuts):
    """Apply Rafael's ruled cuts in place; returns whether R1b is cut."""
    r1b_cut = False
    for cut, units in cuts.items():
        _prove(cut in CUT_ORDER, f"cut {cut!r} is not one of cut_order {CUT_ORDER}")
        _prove(_is_count(units) and units >= 1, f"cut {cut} units {units!r} is not an int >= 1")
        whole = cut not in ("e6_anchor_adapters", "e1_checkpoints")
        _prove(not whole or units == 1, f"cut {cut} takes 1 unit (the whole row), not {units}")
        if cut == "e4_reserve":
            caps["E4"]["points"] = 0
        elif cut == "e6_anchor_adapters":
            left = caps["E6"]["anchor_adapters"] - units
            _prove(left >= 0, f"cut e6_anchor_adapters {units} leaves {left} adapters")
            caps["E6"]["anchor_adapters"] = left
        elif cut == "e2_seeds_to_3":
            _prove(caps["E2"]["seeds"] > MIN_SEEDS, f"S is already {caps['E2']['seeds']}")
            caps["E2"]["seeds"] = MIN_SEEDS
        elif cut == "e3_whole":
            caps["E3"]["recipes"] = 0
        elif cut == "e1_checkpoints":
            left = caps["E1"]["checkpoints_per_cell"] - units
            _prove(left >= 1, f"cut e1_checkpoints {units} leaves {left} checkpoints per cell")
            caps["E1"]["checkpoints_per_cell"] = left
        elif cut == "r1b":
            r1b_cut = True
        else:  # e1_core
            caps["E1"]["cells"] = caps["E1"]["calibrations"] = 0
    return r1b_cut


def derive(
    probes,
    historical,
    *,
    probes_spent_seconds,
    unit_caps=None,
    cuts=None,
    divergences_investigated=None,
    price_rulings=None,
    cap_rulings=None,
):
    """The locked COST-02 arithmetic. Pure: no I/O, no torch, no cut without a ruling."""
    _prove(
        isinstance(probes, dict) and set(probes) == set(phase36_prereg.PROBE_FRONTS),
        f"probes must be keyed by exactly {phase36_prereg.PROBE_FRONTS}",
    )
    for front, record in probes.items():
        device = record["provenance"]["run"]["device"]
        _prove(
            device == PROBE_DEVICE,
            f"probe record {front} ran on {device!r}, not {PROBE_DEVICE!r}: the budget prices "
            "the M3 (COST-01)",
        )
    missing = sorted(set(HISTORICAL_RECORDS) - set(historical))
    _prove(not missing, f"historical records missing: {missing}")
    _prove(
        isinstance(probes_spent_seconds, (int, float))
        and not isinstance(probes_spent_seconds, bool)
        and math.isfinite(probes_spent_seconds)
        and probes_spent_seconds >= 0,
        f"probes_spent_seconds {probes_spent_seconds!r} is not a finite number >= 0",
    )
    findings = dict(divergences_investigated or {})
    cap_rulings = dict(cap_rulings or {})
    price_rulings = dict(price_rulings or {})
    cuts = dict(cuts or {})
    bases = {row["id"] for row in COMPARATORS}
    for key, text in findings.items():
        _prove(key in bases, f"finding for unknown comparator {key!r}")
        _prove(isinstance(text, str) and text.strip(), f"the finding for {key} is empty")

    rows = comparisons(probes, historical)
    for row in rows:
        base = row["id"].split("#")[0]
        _prove(
            not (row["gated"] and row["exceeds"]) or base in findings,
            f"{row['id']}: probe {row['probe_seconds']:.3f} s vs historical "
            f"{row['historical_seconds']:.3f} s diverges {row['divergence']:.1%}, above "
            "divergence_tolerance. D-02/D-04: investigate BEFORE the budget, then pass the "
            f"written finding as divergences_investigated[{base!r}]",
        )

    alternatives = price_alternatives(probes, historical)
    prices = apply_price_rulings(unit_prices(probes, historical), alternatives, price_rulings)
    proposed = proposed_unit_caps(probes)
    caps = proposed if unit_caps is None else unit_caps
    caps = {front: dict(block) for front, block in caps.items()} if isinstance(caps, dict) else caps
    probed_batch = probes["e3"]["configuration"]["batch"]
    _prove_caps(caps, cap_rulings, probed_batch)
    if caps["E3"]["max_batch"] > probed_batch:  # W10: per-step cost linear in batch, a high bound
        prices["e3_per_step_high"] *= caps["E3"]["max_batch"] / probed_batch
    r1b_cut = _apply_cuts(caps, cuts)

    seconds = {"probes": probes_spent_seconds, **_front_seconds(prices, caps, r1b_cut)}
    front_hours = {f: seconds[f] / 3600 for f in phase35_prereg.V6_MPS_FRONTS}
    total = math.fsum(front_hours.values())
    fits = total <= CEILING
    return {
        "front_hours": front_hours,
        "total_hours": total,
        "stop_line_hours": min(STOP_LINE_FACTOR * total, CEILING) if fits else None,
        "e2_seed_count": caps["E2"]["seeds"],
        "unit_caps": caps,
        "unit_prices": prices,
        "price_alternatives": alternatives,
        "price_rulings": price_rulings,
        "cap_rulings": cap_rulings,
        "comparisons": rows,
        "divergences_investigated": findings,
        "cuts_applied": cuts,
        "fits": fits,
        "overflow_hours": None if fits else total - CEILING,
        "cut_table": [] if fits else cut_table(prices, caps, front_hours, total),
        "formula": FORMULA,
    }


# =================================================================================================
# COMMITTED INPUTS — git blobs only — and the fill-file helpers
# =================================================================================================


def _head_blob(rel, tracked):
    """``rel``'s blob at HEAD; refuses an untracked path."""
    _prove(rel in set(tracked), f"{rel} is not TRACKED: only a committed file is read")
    shown = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=_GIT_ROOT, capture_output=True)
    _prove(shown.returncode == 0, f"{rel} has no committed blob at HEAD")
    return shown.stdout


def _ledger_blob(tracked):
    """The ledger's COMMITTED bytes (later appends on disk never change the probes front)."""
    return _head_blob(phase36_ledger.LEDGER_PATH, tracked)


def probe_record_paths(tracked=None):
    """The five probe records, all tracked; a partial set is refused naming the missing fronts."""
    tracked = set(phase36_caps.tracked_files() if tracked is None else tracked)
    missing = [
        f
        for f, p in zip(phase36_prereg.PROBE_FRONTS, phase36_prereg.PROBE_RECORDS)
        if p not in tracked
    ]
    _prove(
        not missing,
        f"probe records missing for fronts {missing} "
        f"({[phase36_prereg.probe_record(f) for f in missing]}): the budget prices five COMMITTED "
        "probe records",
    )
    return phase36_prereg.PROBE_RECORDS


def load_probes(tracked):
    return {
        front: phase30_points._tracked_json(phase36_prereg.probe_record(front), tracked, "probe")
        for front in phase36_prereg.PROBE_FRONTS
    }


def load_historical(tracked):
    return {
        rel: (
            _head_blob(rel, tracked).decode("utf-8")
            if rel.endswith(".md")
            else phase30_points._tracked_json(rel, tracked, "the historical record")
        )
        for rel in HISTORICAL_RECORDS
    }


def ledger_probes_seconds(tracked):
    """W2: the probes front's seconds from the COMMITTED ledger, lost attempts included."""
    _prove(
        phase36_ledger.LEDGER_PATH in set(tracked),
        f"{phase36_ledger.LEDGER_PATH} is not tracked: the probes front is read from the committed "
        "ledger (W2), so commit it first (phase36_probe.py emit-all)",
    )
    with tempfile.TemporaryDirectory() as scratch:
        path = pathlib.Path(scratch) / "ledger.jsonl"
        path.write_bytes(_ledger_blob(tracked))
        spent = phase36_ledger.spent(tracked, ledger_path=path, fronts=("probes",))
    return spent["by_front"]["probes"]


def committed_derive(paths, *, tracked=None, approved=None, **ruling):
    """derive on the COMMITTED records at ``paths``; ``approved`` is accepted and unused (one
    RULING dict splats into chosen, derivation and budget_record)."""
    tracked = phase36_caps.tracked_files() if tracked is None else tracked
    _prove(
        tuple(paths) == probe_record_paths(tracked),
        f"paths {paths} are not the probe records {phase36_prereg.PROBE_RECORDS}",
    )
    return derive(
        load_probes(tracked),
        load_historical(tracked),
        probes_spent_seconds=ledger_probes_seconds(tracked),
        **ruling,
    )


def _fit_value(derived):
    _prove(
        derived["fits"],
        f"HALT: the fronts total {derived['total_hours']:.3f} h and do not fit Rafael's "
        f"{CEILING} h ceiling — take the cut table to Rafael (COST-02, D-15); no front is cut "
        "unilaterally",
    )
    return {
        "front_hours": dict(derived["front_hours"]),
        "stop_line_hours": derived["stop_line_hours"],
        "e2_seed_count": derived["e2_seed_count"],
    }


def chosen(paths, **ruling):
    """The fill's chosen value from committed records; refuses a HALT."""
    return _fit_value(committed_derive(paths, **ruling))


def _describe(ruling):
    lines = [f"formula.{k}: {v}" for k, v in FORMULA.items()]
    caps = ruling.get("unit_caps")
    lines.append(
        "unit_caps: "
        + ("the proposal (CAP_DERIVATIONS)" if caps is None else json.dumps(caps, sort_keys=True))
    )
    lines.append(f"cuts applied: {json.dumps(ruling.get('cuts') or {}, sort_keys=True)}")
    for key, text in sorted((ruling.get("divergences_investigated") or {}).items()):
        lines.append(f"finding {key}: {text}")
    for name, choice in sorted((ruling.get("price_rulings") or {}).items()):
        default = RULING_ALTERNATIVES[name][0]
        lines.append(f"price ruling {name}: {choice} (default {default})")
    for key, text in sorted((ruling.get("cap_rulings") or {}).items()):
        lines.append(f"cap ruling {key}: {text} (default: the probed value)")
    return lines


def derivation(value, paths, **ruling):
    """The four-field derivation for the fill; ``source`` names every input path."""
    unknown = sorted(set(ruling) - set(RULING_KEYS))
    _prove(not unknown, f"unknown ruling keys {unknown}")
    approved = ruling.get("approved")
    _prove(isinstance(approved, str) and approved.strip(), "no approved text from Rafael")
    return {
        "value": value,
        "derivation": "; ".join([*_describe(ruling), f"approved by Rafael: {approved}"]),
        "kind": "derived",
        "source": " ".join(
            [
                *paths,
                *HISTORICAL_RECORDS,
                phase36_ledger.LEDGER_PATH,
                "36-CONTEXT D-01..D-19 and Addendum (43a8432, 5deba79)",
            ]
        ),
    }


def budget_record(filled, derived, ruling):
    """The budget record from the fill's output and derive's; the shape re-proved (D-09)."""
    plain = {
        "front_hours": dict(filled["front_hours"]),
        "total_hours": filled["total_hours"],
        "stop_line_hours": filled["stop_line_hours"],
        "e2_seed_count": filled["e2_seed_count"],
    }
    _prove(
        plain["front_hours"] == derived["front_hours"]
        and plain["stop_line_hours"] == derived["stop_line_hours"]
        and plain["e2_seed_count"] == derived["e2_seed_count"],
        "the filled budget is not the derived one",
    )
    record = {
        **plain,
        "unit_caps": derived["unit_caps"],
        "cap_derivations": CAP_DERIVATIONS,
        "unit_prices": derived["unit_prices"],
        "price_alternatives": derived["price_alternatives"],
        "price_rulings": derived["price_rulings"],
        "cap_rulings": derived["cap_rulings"],
        "comparisons": derived["comparisons"],
        "formula": derived["formula"],
        "cuts_applied": derived["cuts_applied"],
        "divergences_investigated": derived["divergences_investigated"],
        "approved": ruling.get("approved"),
        "note": RESOURCE_NOT_OUTCOME,
    }
    return phase36_caps.prove_budget_shape(record)


# =================================================================================================
# dry (writes nothing), the precede refusal, the write-once emit, the CLI
# =================================================================================================


def _show(label, value):
    print(f"[phase36_budget] {label}: {json.dumps(value, sort_keys=True)}", flush=True)


def dry(ruling_path=None):
    """Every number for Rafael's checkpoint, from committed files. Writes NOTHING."""
    tracked = phase36_caps.tracked_files()
    paths = probe_record_paths(tracked)  # zero records: the refusal names the missing fronts
    ruling = {}
    if ruling_path is not None:
        ruling_path = pathlib.Path(ruling_path).resolve()
        _prove(
            not ruling_path.is_relative_to(_GIT_ROOT / "results"),
            "a ruling file never lives under results/",
        )
        ruling = json.loads(ruling_path.read_text(encoding="utf-8"))
        unknown = sorted(set(ruling) - set(RULING_KEYS))
        _prove(not unknown, f"unknown ruling keys {unknown}")
    kwargs = {k: v for k, v in ruling.items() if k != "approved"}
    probes, historical = load_probes(tracked), load_historical(tracked)
    spent = ledger_probes_seconds(tracked)
    _show("inputs", [*paths, *HISTORICAL_RECORDS, phase36_ledger.LEDGER_PATH])
    for row in comparisons(probes, historical):
        _show("comparison", row)
    derived = derive(probes, historical, probes_spent_seconds=spent, **kwargs)
    _show("unit_prices", derived["unit_prices"])
    _show("unit_caps", derived["unit_caps"])
    for name, text in CAP_DERIVATIONS.items():
        _show(f"cap {name}", text)
    _show("front_hours", derived["front_hours"])
    _show("total_hours", derived["total_hours"])
    _show("stop_line_hours", derived["stop_line_hours"])
    _show("e2_seed_count", derived["e2_seed_count"])
    for text in SURFACED:
        _show("surfaced for Rafael", text)
    for name, pair in RULING_ALTERNATIVES.items():
        for choice in pair:
            rulings = {**(kwargs.get("price_rulings") or {}), name: choice}
            try:
                alt = derive(
                    probes,
                    historical,
                    probes_spent_seconds=spent,
                    **{**kwargs, "price_rulings": rulings},
                )
            except SystemExit as refused:
                _show(f"ruling {name}={choice}", str(refused))
                continue
            _show(
                f"ruling {name}={choice}",
                {"front_hours": alt["front_hours"], "total_hours": alt["total_hours"]},
            )
    for recipes in (E3_RECIPES, E3_RECIPES + 1):
        caps = {f: dict(b) for f, b in derived["unit_caps"].items()}
        caps["E3"]["recipes"] = recipes
        alt = derive(
            probes, historical, probes_spent_seconds=spent, **{**kwargs, "unit_caps": caps}
        )
        _show(f"E3 hours at recipes {recipes}", alt["front_hours"]["E3"])
    _show(
        "E3 max_batch",
        f"{derived['unit_caps']['E3']['max_batch']} (the probed batch; a larger batch needs "
        "cap_rulings['E3.max_batch'], priced linearly per step, W10)",
    )
    if derived["fits"]:
        print("[phase36_budget] FITS", flush=True)
    else:
        print(
            f"[phase36_budget] HALT: {derived['overflow_hours']:.3f} h over the {CEILING} h "
            "ceiling — the cut table goes to Rafael; nothing is cut without his ruling",
            flush=True,
        )
        for row in derived["cut_table"]:
            _show("cut", row)
    return derived


def later_records(tracked):
    """Tracked records named by a ledger end line of phase >= 37 (the budget must precede them)."""
    tracked = set(tracked)
    return sorted(
        {
            line["record"]
            for line in phase36_ledger.read_ledger()
            if line["event"] == "end" and line["phase"] >= 37 and line["record"] in tracked
        }
    )


def emit(out_path=BUDGET_RECORD):
    """Write-once: overwrite, dirty, fill file, precede refusals; re-derive; prove; write."""
    out_path = pathlib.Path(out_path)
    if not out_path.is_absolute():
        out_path = _GIT_ROOT / out_path
    _prove(
        not out_path.exists(),
        f"{out_path} exists — REFUSING to overwrite it. The budget is write-once; corrections are "
        "dated continuations",
    )
    pathspec = ("scripts", "src", "results")
    if out_path.is_relative_to(_GIT_ROOT):
        pathspec += (f":(exclude){out_path.relative_to(_GIT_ROOT).as_posix()}",)
    refuse_if_dirty(
        who="phase36_budget",
        detail=(
            "the budget publishes git_sha and hashes its pinned modules from the working tree; a "
            "record written from a dirty tree names a commit it cannot be regenerated from"
        ),
        pathspec=pathspec,
        cwd=_GIT_ROOT,
    )
    tracked = phase36_caps.tracked_files()
    _prove(FILL_FILE in tracked, f"{FILL_FILE} is not tracked: commit it after Rafael's approved")
    unchanged = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", FILL_FILE], cwd=_GIT_ROOT)
    _prove(unchanged.returncode == 0, f"{FILL_FILE} differs from its committed blob")
    later = later_records(tracked)
    _prove(
        not later,
        f"{later} already tracked: the budget precedes every phase-37..43 MPS record",
    )
    import phase36_budget_prereg as fill_file  # lazy: exists only after Rafael's approved

    paths = probe_record_paths(tracked)
    derived = committed_derive(paths, tracked=tracked, **fill_file.RULING)
    value = _fit_value(derived)
    filled = fill_file.V6_BUDGET_AND_STOP_LINE
    _prove(
        value
        == {
            "front_hours": dict(filled["front_hours"]),
            "stop_line_hours": filled["stop_line_hours"],
            "e2_seed_count": filled["e2_seed_count"],
        },
        "the fill file's V6_BUDGET_AND_STOP_LINE is not the re-derived budget",
    )
    record = budget_record(filled, derived, fill_file.RULING)
    read = [*paths, *HISTORICAL_RECORDS, phase36_ledger.LEDGER_PATH]
    record["sources"] = {rel: hashlib.sha256(_head_blob(rel, tracked)).hexdigest() for rel in read}
    record["provenance"] = {
        "module_sha256": {
            rel: hashlib.sha256((_GIT_ROOT / rel).read_bytes()).hexdigest()
            for rel in (
                "scripts/phase36_budget.py",
                FILL_FILE,
                "scripts/phase36_prereg.py",
                "scripts/phase36_caps.py",
            )
        },
        "git_sha": INSTRUMENT_GIT_SHA,
        "head_at_write": git_sha(),
        "written_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    phase25_run.atomic_write_json(out_path, record)
    print(f"[phase36_budget] stop line {record['stop_line_hours']:.3f} h — wrote {out_path}")
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description="The v6.0 MPS budget (COST-02).")
    sub = parser.add_subparsers(dest="mode", required=True)
    dry_parser = sub.add_parser("dry", help="print every number; writes nothing")
    dry_parser.add_argument("--ruling", default=None, help="a ruling JSON (never under results/)")
    sub.add_parser("emit", help="write results/phase36_budget.json after the fill file")
    args = parser.parse_args(argv)
    if args.mode == "dry":
        dry(args.ruling)
    else:
        emit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
