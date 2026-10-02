"""Phase 36 pre-registration: every threshold Rafael ruled for the MPS cost probes and the budget.

Committed BEFORE any ``results/phase36_*`` file (COST-01 SC4, PREREG-06): the 25% divergence rule,
the T <= 800 step cap, the E4 reserve, the stop factors, the projection check, S >= 3 for the cut
table and the cut order are frozen before the first probe measures anything, so no threshold can be
tuned to the probe numbers (36-CONTEXT D-17).

Every threshold is an entry with exactly four fields, ``value``, ``derivation``, ``kind`` and
``source`` (no proposer, PREREG-07); preferences carry ``kind = "preference"``. Historical
wall-clocks are named by record path and key path only, never retyped: the tests resolve each one on
the committed record.

This module holds NO fill call: the budget fill comes later, in its own file, after Rafael writes
approved (36-CONTEXT Addendum Q4). It reads only PUBLIC names of the closed v6.0 pre-registration
and imports without torch.
"""

import collections.abc
import fnmatch
import math
import pathlib
import sys
import types

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_SRC = str(_REPO_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import phase25_record  # noqa: E402  (needs the sys.path insert above; torch-free)
import phase35_prereg  # noqa: E402  (same; torch-free)

# =================================================================================================
# (1) THE DATE AND THE PROPERTY IT CERTIFIES.
# =================================================================================================

# At this commit no `results/phase36_*` file existed, tracked or untracked.
COMMITTED = "2026-10-02"
RECORDS_AT_COMMIT = 0


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase36_prereg] {message}")


# =================================================================================================
# (2) THE ENTRY SCHEMA, BY REFERENCE to the v6.0 pre-registration's public tuples.
# =================================================================================================

ENTRY_FIELDS = phase35_prereg.ENTRY_FIELDS
KINDS = phase35_prereg.KINDS
FORBIDDEN_PHRASE = phase35_prereg.FORBIDDEN_PHRASE


def _prove_entry(name, entry):
    """Refuse any entry that is not exactly the four fields with a known kind."""
    _prove(
        isinstance(entry, collections.abc.Mapping),
        f"entry {name!r} is {type(entry).__name__}, not a mapping",
    )
    for banned in ("proposer", "adopted_by"):
        _prove(
            banned not in entry,
            f"entry {name!r} carries a {banned!r} key. Entries hold exactly {ENTRY_FIELDS}; who "
            "suggested what lives in the discussion logs and git",
        )
    _prove(
        set(entry) == set(ENTRY_FIELDS),
        f"entry {name!r} has fields {sorted(entry)}, expected exactly {sorted(ENTRY_FIELDS)}",
    )
    _prove(entry["kind"] in KINDS, f"entry {name!r} has kind {entry['kind']!r}, not one of {KINDS}")
    for field in ("derivation", "source"):
        text = entry[field]
        _prove(
            isinstance(text, str) and text.strip(),
            f"entry {name!r} has an empty or non-str {field}",
        )
        _prove(
            FORBIDDEN_PHRASE not in text, f"entry {name!r} {field} contains {FORBIDDEN_PHRASE!r}"
        )
    value = entry["value"]
    _prove(
        not (isinstance(value, str) and FORBIDDEN_PHRASE in value),
        f"entry {name!r} value contains {FORBIDDEN_PHRASE!r}",
    )


# =================================================================================================
# (3) THE PROBE RECORD PATHS (D-16), fixed here before any record, derived from V6_RESULT_PATHS.
# =================================================================================================

PROBE_GLOB = next(
    p for p in phase35_prereg.V6_RESULT_PATHS if p.startswith("results/phase36_probe_")
)
PROBE_FRONTS = ("e1", "e2", "e3", "e5", "e6")
PROBE_RECORDS = tuple(PROBE_GLOB.replace("*", front) for front in PROBE_FRONTS)


def probe_record(front):
    """The probe record path for one front, or a refusal for an unknown front."""
    _prove(front in PROBE_FRONTS, f"front {front!r} has no probe record; probed: {PROBE_FRONTS}")
    return PROBE_RECORDS[PROBE_FRONTS.index(front)]


for _path in PROBE_RECORDS:
    _prove(fnmatch.fnmatch(_path, PROBE_GLOB), f"{_path} does not match {PROBE_GLOB}")
    _prove(
        not any(
            fnmatch.fnmatch(_path, pattern)
            for pattern in phase35_prereg.V6_RESULT_PATHS
            if pattern != PROBE_GLOB
        ),
        f"{_path} collides with another v6.0 record pattern (probe isolation)",
    )

# The E3 probe point (D-05: "an already-published sigma"): the dp_n8 arm at the first noised sigma,
# built the way the v6.0 pre-registration builds its v4.0 control record path.
E3_PROBE_POINT_KEY = phase25_record.point_key(
    f"dp_n{phase35_prereg.E3_N}", phase35_prereg.E3_SIGMAS[1]
)
E3_PROBE_POINT_RECORD = str(
    phase25_record.point_record_path(E3_PROBE_POINT_KEY).relative_to(_REPO_ROOT)
)

# =================================================================================================
# (4) THE ENTRIES (D-17, D-19, Q5).
# =================================================================================================

_CONTEXT = "36-CONTEXT D-{} (43a8432)"
_ADDENDUM = "36-CONTEXT Addendum D-18/D-19/Q5 (5deba79)"


def _row(id_, front, probe_field, historical_path, historical_key, unit, gated):
    return types.MappingProxyType(
        {
            "id": id_,
            "front": front,
            "probe_field": probe_field,
            "historical_path": historical_path,
            "historical_key": historical_key,
            "unit": unit,
            "gated": gated,
        }
    )


_ENTRIES = {
    "divergence_tolerance": {
        "value": 0.25,
        "derivation": (
            "D-02: |probe - historical| / historical > value means investigate BEFORE the budget "
            "is committed; for R1b (D-04) it means STOP and investigate. Applied mechanically "
            "through the divergence_comparators rows."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('02')}; {_CONTEXT.format('04')}",
    },
    "divergence_comparators": {
        "value": (
            _row(
                "r1b_e1_k48",
                "E1",
                "runs[*].total_seconds",
                "results/phase19_arm_erased.json",
                ("config", "wall_clock_min"),
                "min",
                True,
            ),
            _row(
                "e2_a2_pass",
                "E2",
                "a2_pass.total_seconds",
                "results/phase19_arm_retrain.json",
                ("config", "wall_clock_min"),
                "min",
                True,
            ),
            _row(
                "e3_t200_train",
                "E3",
                "t_step_budget.train_seconds",
                E3_PROBE_POINT_RECORD,
                ("training", "seconds"),
                "s",
                True,
            ),
            _row(
                "e3_t200_score",
                "E3",
                "t_step_budget.score_seconds",
                "results/phase25_recall.json",
                ("points", E3_PROBE_POINT_KEY, "scoring_seconds"),
                "s",
                True,
            ),
            _row(
                "e3_t800_linearity",
                "E3",
                "t_max_steps.loop_seconds vs (t_max_steps.steps / t_step_budget.steps) x "
                "t_step_budget.loop_seconds",
                None,
                None,
                "s",
                True,
            ),
            _row(
                "e5_clearance",
                "E5",
                "clearance.total_seconds",
                "results/phase17_personas_report.md",
                r"wall `([0-9.]+)` min",
                "min",
                True,
            ),
            _row(
                "e2_training_context",
                "E2",
                "train reps outer_seconds",
                "results/phase23_control_floor.json",
                ("per_seed", "*", "training_seconds"),
                "s",
                False,
            ),
            _row(
                "e1_phase31_beside",
                "E1",
                None,
                "results/phase31_probe_point.json",
                ("total_seconds",),
                "s",
                False,
            ),
        ),
        "derivation": (
            "D-02/D-04/D-05/D-08: each gated row compares one probe field with the historical "
            "wall-clock at historical_path::historical_key under divergence_tolerance. R1b's "
            "comparator is the Phase 19 erased arm (k = 78, K = 48, seed 1337). e3_t800_linearity "
            "is D-05's linearity check (T = 800 against T = 200 scaled by steps). Ungated rows are "
            "context only: e2_training_context is a different arm on the same teach_persona "
            "recipe; e1_phase31_beside is the Phase 31 probe, a different reading recorded beside "
            "the E1 probe, never compared and never extrapolated from (COST-01, D-03), so it is "
            "EXCLUDED from every 25% comparison and is the only row without a probe_field. A "
            "historical_key that is a str is a regex over a markdown report."
        ),
        "kind": "derived",
        "source": (
            f"{_CONTEXT.format('02/D-03/D-04/D-05/D-08')}; results/phase19_arm_erased.json, "
            "results/phase19_arm_retrain.json, results/phase25_point_dp_n8_sigma0p500000.json, "
            "results/phase25_recall.json, results/phase17_personas_report.md, "
            "results/phase23_control_floor.json, results/phase31_probe_point.json"
        ),
    },
    "uncompared_stages": {
        "value": (
            ("E5 per-candidate NLL scoring", "no per-candidate time on record"),
            ("E6 anchor generation", "no published configuration (D-07)"),
            ("E4 canary scoring", "priced from the record, NOT re-measured (D-19)"),
            ("E1 ordering", "priced from the record, NOT re-measured (Q5)"),
            ("E1 calibration", "priced from records, NOT re-measured"),
        ),
        "derivation": (
            "D-02 compares a probe with a historical wall-clock only where one exists on record; "
            "these stages have none to compare, or are priced from a record and not probed."
        ),
        "kind": "derived",
        "source": f"{_CONTEXT.format('02/D-07')}; {_ADDENDUM}",
    },
    "e3_max_steps": {
        "value": 4 * phase35_prereg.STEP_BUDGET,
        "derivation": (
            "D-05: the E3 step-count cap is 4x v4.0's STEP_BUDGET. The P22 assertion (RECIPE-04) "
            "holds at this T: prove_p22 runs at import."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('05')}; scripts/mitigation_budget.py STEP_BUDGET",
    },
    "e3_probe_steps": {
        "value": (phase35_prereg.STEP_BUDGET, 4 * phase35_prereg.STEP_BUDGET),
        "derivation": (
            "D-05: T = STEP_BUDGET trains and scores on the published v4.0 recipe; T = "
            "e3_max_steps trains only (timing). Scoring does not depend on T, so it comes from "
            "the first run."
        ),
        "kind": "derived",
        "source": _CONTEXT.format("05"),
    },
    "e4_reserve_points": {
        "value": 3,
        "derivation": (
            "D-06: each point is one T = STEP_BUDGET training run plus scoring. E4 audits v4.0's "
            "epsilon claims, made at T = 200 with the v4.0 recipe, and the audit changes only "
            "canary inclusion; auditing another recipe is another front and needs Rafael's "
            "approved. If Phase 43 cuts E4 (AUDIT-02) the hours stay unused and are never "
            "reallocated without Rafael's approved."
        ),
        "kind": "preference",
        "source": _CONTEXT.format("06"),
    },
    "e4_canary_scoring_price": {
        "value": (
            "results/phase26_canary_sources.json",
            ("points", E3_PROBE_POINT_KEY, "provenance", "scoring_seconds"),
        ),
        "derivation": (
            "D-19: E4's canary-scoring stage is read from the record and used as the high bound; "
            "it was NOT re-measured. E4 per point = T = STEP_BUDGET training from the E3 probe + "
            "this scoring, times e4_reserve_points."
        ),
        "kind": "derived",
        "source": f"{_ADDENDUM}; results/phase26_canary_sources.json",
    },
    "e4_first_point_check": {
        "value": types.MappingProxyType(
            {"tolerance_entry": "divergence_tolerance", "price_key": "e4_point_seconds"}
        ),
        "derivation": (
            "D-19, an obligation carried to Phase 43: if E4 runs, its first point is timed and "
            "compared with the reserve's per-point price before the rest launch; a divergence "
            "above the tolerance pauses and goes back to Rafael."
        ),
        "kind": "preference",
        "source": _ADDENDUM,
    },
    "e1_ordering_price": {
        "value": ("results/phase19_collateral_curve.json", ("wall_clock_min",)),
        "derivation": "Q5: each E1 cell's ordering cost, read from the record; NOT re-measured.",
        "kind": "derived",
        "source": f"{_ADDENDUM}; results/phase19_collateral_curve.json",
    },
    "e1_calibration_price": {
        "value": types.MappingProxyType(
            {
                "curve": ("results/phase19_calibration_curve.json", ("wall_clock_min",)),
                "arm": ("results/phase19_arm_cal-erased.json", ("config", "wall_clock_min")),
            }
        ),
        "derivation": (
            "ERASE-06's per-(ordering, seed) calibration (35-05) is priced as one calibration "
            "training (the E2 training unit) + the calibration curve + the cal-erased arm, NOT "
            "re-measured: the Q5 pattern applied as the plan-time DEFAULT and surfaced to Rafael "
            "at the budget checkpoint. His ruling may replace it with the probe_scaled alternative "
            "listed in high_bound_rule's ruling_alternatives; a replacement is recorded in the "
            "budget derivation (W5)."
        ),
        "kind": "derived",
        "source": (
            f"{_ADDENDUM}; results/phase19_calibration_curve.json, "
            "results/phase19_arm_cal-erased.json"
        ),
    },
    "high_bound_rule": {
        "value": types.MappingProxyType(
            {
                "H1": "a unit measured in >= 2 repetitions prices at the MAX repetition",
                "H2": (
                    "a single run of a draw loop (the E2 A2 pass, the E3 score_arm pass) prices "
                    "from its OWN per-draw distribution: its non-draw seconds + questions x the "
                    "MAX per-question draw seconds, the per-question blocks read from its "
                    "DrawTimer rows"
                ),
                "H3": (
                    "a unit repeated in blocks within one run (E5 clearance per slot, E5 NLL per "
                    "slot x adapter, E6 anchor draws per slot) prices at the max block mean"
                ),
                "ruling_alternatives": types.MappingProxyType(
                    {
                        "a2_draw_basis": ("k78", "at_cap"),
                        "single_run_draw_loop": ("within_run", "spread_scaled"),
                        "e1_calibration": ("records", "probe_scaled"),
                    }
                ),
            }
        ),
        "derivation": (
            "D-02/D-10 made mechanical. Each rule is the plan-time DEFAULT; Rafael's ruling at the "
            "budget checkpoint may replace it with the listed alternative, the replacement "
            "recorded in the budget derivation (W5). ruling_alternatives maps name -> (default, "
            "alternative): a2_draw_basis at_cap prices E1's per-draw cost at the MAX at-cap draw "
            "seconds (D-10's high bound), because checkpoints deeper than k = 78 can cost more "
            "(36-RESEARCH depth-dependence warning), while R1b is always the measured k = 78 "
            "reading; single_run_draw_loop spread_scaled prices the run total x max / min of the "
            "two E1 K = 48 run totals; e1_calibration probe_scaled takes e1_calibration_price's "
            "record minutes x (max E1 K = 48 total / the erased-arm record's wall-clock)."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('02/D-10')}; {_ADDENDUM}",
    },
    "front_stop_factor": {
        "value": 1.5,
        "derivation": (
            "D-13a: a front that passes this factor x its own high bound pauses and goes to "
            "Rafael (the Phase 31 precedent)."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('13')}; results/phase31_budget.json",
    },
    "stop_line_factor": {
        "value": 1.5,
        "derivation": (
            "D-13b: stop_line_hours = min(stop_line_factor x sum(front_hours), mps_ceiling_hours); "
            "the Phase 31 rule applied milestone-wide and capped by the ceiling."
        ),
        "kind": "preference",
        "source": _CONTEXT.format("13"),
    },
    "projection_rule": {
        "value": (
            "before each launch: sum over V6_MPS_FRONTS f of max(front_hours[f], spent_hours[f]) "
            "<= mps_ceiling_hours, else pause BEFORE launching and bring the cut table"
        ),
        "derivation": (
            "D-13c: ledger hours spent + the high bounds of the remaining fronts must fit the "
            "ceiling; no front starts unless it fits whole in the projection. The max form equals "
            "spent + the remaining high bounds."
        ),
        "kind": "preference",
        "source": _CONTEXT.format("13"),
    },
    "cut_table_min_seeds": {
        "value": 3,
        "derivation": (
            "D-14: S below this never enters the cut table without asking Rafael; stricter than "
            "the v6.0 e2_min_seeds."
        ),
        "kind": "preference",
        "source": _CONTEXT.format("14"),
    },
    "e2_proposed_seed_count": {
        "value": 5,
        "derivation": "D-14: the proposal sets S = 5; nothing is reduced automatically.",
        "kind": "preference",
        "source": _CONTEXT.format("14"),
    },
    "cut_order": {
        "value": (
            "e4_reserve",
            "e6_anchor_adapters",
            "e2_seeds_to_3",
            "e3_whole",
            "e1_checkpoints",
            "r1b",
            "e1_core",
        ),
        "derivation": (
            "D-15 read literally: the rows go in Rafael's order and R1b and the E1 core are last, "
            "the last two rows; like every other row each carries the hours it saves and the "
            "scientific question it loses. No row is ever applied without Rafael's ruling (Claude "
            "never cuts on its own). S below cut_table_min_seeds is never a row (D-14)."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('15')}; {_CONTEXT.format('14')}",
    },
}

ENTRIES = types.MappingProxyType(
    {name: types.MappingProxyType(entry) for name, entry in _ENTRIES.items()}
)


def _prove_entries():
    for name, entry in ENTRIES.items():
        _prove_entry(name, entry)


_prove_entries()

# =================================================================================================
# (5) THE RULES, MECHANICAL.
# =================================================================================================


def divergence(probe_seconds, historical_seconds):
    """|probe - historical| / historical (D-02), on finite inputs with historical > 0."""
    for name, value in (("probe", probe_seconds), ("historical", historical_seconds)):
        _prove(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value),
            f"{name} seconds is {value!r}, not a finite number",
        )
    _prove(historical_seconds > 0, f"historical seconds is {historical_seconds!r}; need > 0")
    return abs(probe_seconds - historical_seconds) / historical_seconds


def exceeds(probe_seconds, historical_seconds):
    """True iff the divergence is above ``divergence_tolerance`` (investigate / STOP)."""
    return divergence(probe_seconds, historical_seconds) > ENTRIES["divergence_tolerance"]["value"]


def prove_p22(steps):
    """RECIPE-04: the P22 onset at T = ``steps`` lies below the smallest noised E3 sigma."""
    onset = phase35_prereg.p22_onset_sigma(steps)
    smallest = min(s for s in phase35_prereg.E3_SIGMAS if s > 0)
    _prove(
        onset < smallest,
        f"RECIPE-04: the P22 onset at T = {steps} is {onset}, not below the smallest noised E3 "
        f"sigma {smallest}",
    )
    return onset


_prove(
    ENTRIES["cut_table_min_seeds"]["value"] >= phase35_prereg.ENTRIES["e2_min_seeds"]["value"],
    "cut_table_min_seeds is below the v6.0 e2_min_seeds (D-14: stricter, never looser)",
)
_prove(
    ENTRIES["e2_proposed_seed_count"]["value"] >= ENTRIES["cut_table_min_seeds"]["value"],
    "e2_proposed_seed_count is below cut_table_min_seeds",
)
prove_p22(ENTRIES["e3_max_steps"]["value"])
