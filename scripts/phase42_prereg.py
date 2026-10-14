"""Phase 42 pre-registration, fill file 1: E3's grid of DP-SGD recipes, the record paths and every
written decision, frozen before any ``results/phase42_*`` record (42-CONTEXT D-01..D-23;
RECIPE-01..RECIPE-04).

Owner 42, ``scripts/phase42_*prereg.py``. This module fills ``e3_grid_subset``, the only Phase 42
slot with no in-phase input. Under the Phase 35 slot-ordering leg (a) every commit touching this
file must therefore strictly precede the first add of every ``results/phase42_*`` record. The
threshold slot ``e3_recall_threshold`` is filled later, in ``scripts/phase42_threshold_prereg.py``,
after the three new sigma = 0 control records are committed (D-19).

Importing this module re-runs the reused v4.0 control's SHA-256 check against tag v5.0 and the P22
check for every T the grid uses (RECIPE-04), both inside the Phase 35 grid rule. It writes nothing
at import (tests/test_phase36_caps.py executes it in a fresh module). Not torch-free at import:
``teach_persona`` and ``seed_list()`` load torch.

Plans 42-02 and 42-03 add the pure functions to this same file; plan 42-06's review with Rafael runs
before any run. Once any ``results/phase42_*`` record is tracked this file is closed: any correction
is Rafael's ruling plus a dated continuation (``scripts/_addendum.py``), never an edit.

Every entry has exactly four fields, ``value``, ``derivation``, ``kind`` and ``source`` (no
proposer). Steps, batch, seed, counts, prices and onsets are read from the modules and records that
own them, never typed; lr = 1e-3 is the one caller-chosen literal (D-02).
"""

import collections.abc
import fnmatch
import hashlib
import json
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

import mitigation_budget  # noqa: E402  (needs the sys.path insert above; torch-free)
import phase25_record  # noqa: E402  (same; torch-free)
import phase29_prereg  # noqa: E402  (same; torch-free, loaded by phase35_prereg)
import phase35_prereg  # noqa: E402  (same)
import phase36_caps  # noqa: E402  (same; torch-free)
import phase36_prereg  # noqa: E402  (same)
import teach_persona  # noqa: E402  (same; torch at import)

# =================================================================================================
# (1) THE DATE AND THE PROPERTY IT CERTIFIES.
# =================================================================================================

# At this commit no `results/phase42_*` file existed, tracked or untracked.
COMMITTED = "2026-10-13"
RECORDS_AT_COMMIT = 0


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase42_prereg] {message}")


# =================================================================================================
# (2) THE ENTRY SCHEMA, BY REFERENCE to the v6.0 pre-registration's public tuples.
# =================================================================================================

ENTRY_FIELDS = phase35_prereg.ENTRY_FIELDS
KINDS = phase35_prereg.KINDS
FORBIDDEN_PHRASE = phase35_prereg.FORBIDDEN_PHRASE


def _prove_count(name, value, low=0):
    """An ``int`` (bool excluded) of at least ``low``, never a float out of arithmetic."""
    _prove(
        isinstance(value, int) and not isinstance(value, bool) and value >= low,
        f"{name} is {value!r}, not an int >= {low} (bool excluded)",
    )


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


def _read(rel):
    """A committed JSON record, by repository-relative path."""
    return json.loads((_REPO_ROOT / rel).read_text(encoding="utf-8"))


# =================================================================================================
# (3) THE RECORD GLOBS, from the paths the v6.0 pre-registration reserved (selected by EQUALITY),
# and the inputs its registry declares for the grid slot.
# =================================================================================================

RECORD_GLOB = next(p for p in phase35_prereg.V6_RESULT_PATHS if p == "results/phase42_*")
CONTROL_GLOB = next(
    p for p in phase35_prereg.V6_RESULT_PATHS if p == "results/phase42_control_*.json"
)
BUDGET_RECORD = phase35_prereg.SLOTS["e3_grid_subset"]["input_records"][0]
V4_CONTROL_RECORD = phase35_prereg.SLOTS["e3_grid_subset"]["input_records"][1]

_BUDGET = _read(BUDGET_RECORD)
_V4 = _read(V4_CONTROL_RECORD)

# D-03: the reused control, read from its committed bytes (the Phase 35 rule compares the same
# bytes with `git show v5.0:` at every import of this file).
V4_CONTROL_SHA256 = hashlib.sha256((_REPO_ROOT / V4_CONTROL_RECORD).read_bytes()).hexdigest()
V4_CONTROL_COUNTS = types.MappingProxyType(
    {
        "taught": (_V4["taught_recall"]["numerator"], _V4["taught_recall"]["denominator"]),
        "heldout": (_V4["heldout_recall"]["numerator"], _V4["heldout_recall"]["denominator"]),
    }
)

# =================================================================================================
# (4) THE GRID (RECIPE-01; D-01, D-02, D-04): lr x T at batch teach_persona.BATCH_SIZE (q = 1),
# one seed for the whole grid.
# =================================================================================================

SEED = phase35_prereg.seed_list()[0]
T_MAX = phase36_prereg.ENTRIES["e3_max_steps"]["value"]
# D-02: 1e-3 is caller-chosen, the one typed literal of this file.
LRS = (teach_persona.LR, 1e-3)
STEPS = (phase35_prereg.STEP_BUDGET, T_MAX)
# RECIPES[0] is the v4.0 recipe. MappingProxyType, never dict: an entry value holds no mutable
# container; the Phase 35 rule accepts any Mapping.
RECIPES = tuple(
    types.MappingProxyType({"lr": lr, "steps": t, "batch": teach_persona.BATCH_SIZE})
    for lr in LRS
    for t in STEPS
)
CONTROL_SIGMA = phase35_prereg.E3_SIGMAS[0]
NOISED_SIGMAS = tuple(s for s in phase35_prereg.E3_SIGMAS if s > CONTROL_SIGMA)

# D-05: warmup at the v4.0 shape, WARMUP_STEPS / MAX_STEPS of T (20 at T = 200, 80 at T = 800).
WARMUPS = types.MappingProxyType(
    {t: t * teach_persona.WARMUP_STEPS // teach_persona.MAX_STEPS for t in STEPS}
)

# D-09: every cell trains except the reused v4.0 control (RECIPES[0] at CONTROL_SIGMA); proved
# equal to the fill's non-reused cells below.
_TRAINED_STEPS = tuple(
    recipe["steps"]
    for recipe in RECIPES
    for sigma in phase35_prereg.E3_SIGMAS
    if not (recipe is RECIPES[0] and sigma == CONTROL_SIGMA)
)
_PRICES = _BUDGET["unit_prices"]
_PRICED_HOURS = sum(
    (_PRICES["e3_overhead_high"] + t * _PRICES["e3_per_step_high"] + _PRICES["e3_score_high"])
    / 3600
    for t in _TRAINED_STEPS
)

# D-16: the v4.0 recipe's noised readings, from the recall record (the point records carry no
# recall fields); keys built with phase25_record.point_key, never typed.
_RECALL_RECORD = "results/phase25_recall.json"
_RECALL_POINTS = _read(_RECALL_RECORD)["points"]
_V4_NOISED_KEYS = tuple(
    phase25_record.point_key(f"dp_n{phase35_prereg.E3_N}", sigma) for sigma in NOISED_SIGMAS
)
_D16_READINGS = "; ".join(
    f"{key}: {point['taught_recall']['numerator']}/{point['taught_recall']['denominator']} "
    f"taught, {point['heldout_recall']['numerator']}/{point['heldout_recall']['denominator']} "
    "held-out"
    for key, point in ((key, _RECALL_POINTS[key]) for key in _V4_NOISED_KEYS)
)
_NOISED_CELLS = len(RECIPES) * len(NOISED_SIGMAS)

# =================================================================================================
# (5) THE ENTRIES: one entry per decision.
# =================================================================================================

_CONTEXT = "42-CONTEXT D-{} (dc578f9)"
# D-18 corrected and D-23 added by Rafael's ruling in plan-phase, 2026-10-13 (the commit whose
# 42-CONTEXT first holds "D-23: Each point publishes"; proved by tests/test_phase42_prereg.py).
_RULING_CONTEXT = "42-CONTEXT D-{} (4f45a91)"
_RULING = "plan-phase ruling 2026-10-13 (42-RESEARCH Open Questions)"
_DEFAULT = "default taken at plan time, not yet confirmed by Rafael"

_ENTRIES = {
    "e3_grid_subset": {
        "value": RECIPES,
        "derivation": (
            "RECIPE-01, D-01: batch fixed at teach_persona.BATCH_SIZE, so q = 1; the accountant is "
            "frozen at q = 1 (src/personacore/privacy/accountant.py:850, where a penalty out of "
            "caution is still a wrong published number). D-02: a 2x2 factorial, lr in "
            "(teach_persona.LR, 1e-3) x T in (phase35_prereg.STEP_BUDGET, "
            "phase36_prereg.ENTRIES['e3_max_steps']), batch 8; the v4.0 corner (lr 3e-4, T = 200, "
            "batch 8) is one of the 4, inside unit_caps.E3. D-03: the v4.0 sigma = 0 control is "
            "reused by SHA-256 against tag v5.0, consumed as a declared input of this fill; only "
            "the record is reused, never the adapter. D-09: no fifth recipe; the recipes cap "
            "stays at 4."
        ),
        "kind": "preference",
        "source": (
            "42-CONTEXT D-01, D-02, D-03, D-09 (dc578f9); "
            f"{BUDGET_RECORD} front_hours.E3, unit_caps.E3; {V4_CONTROL_RECORD}"
        ),
    },
    "batch_and_q": {
        "value": teach_persona.BATCH_SIZE,
        "derivation": (
            "D-01: batch fixed at teach_persona.BATCH_SIZE, so q = 1; the v4.0 point published "
            "accounting.q = 1.0 and composed_lot_sizes [8]. Batch < 8 with a subsampled "
            "accountant is a new capability, deferred outside v6.0."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('01')}; {V4_CONTROL_RECORD} accounting",
    },
    "v4_control_reuse": {
        "value": types.MappingProxyType(
            {
                "record": V4_CONTROL_RECORD,
                "sha256": V4_CONTROL_SHA256,
                "taught": V4_CONTROL_COUNTS["taught"],
                "heldout": V4_CONTROL_COUNTS["heldout"],
                "seed": _V4["seed"],
            }
        ),
        "derivation": (
            "D-03: the v4.0 sigma = 0 control is reused, verified through the Phase 35 grid rule "
            "(git show v5.0, sha256 of the committed bytes) at every import of this file; only the "
            "record (its recall) is reused, never the adapter. Its sha256, counts and seed are "
            "read from the record here, never typed."
        ),
        "kind": "derived",
        "source": f"{_CONTEXT.format('03')}; {V4_CONTROL_RECORD}; tag v5.0",
    },
    "one_seed": {
        "value": SEED,
        "derivation": (
            "D-04: declared limit, one seed (phase35_prereg.seed_list()[0]) for the whole grid. "
            "Phase 40 measured variation between seeds, so no E3 result is claimed for any other "
            "seed."
        ),
        "kind": "preference",
        "source": _CONTEXT.format("04"),
    },
    "warmup_rule": {
        "value": WARMUPS,
        "derivation": (
            "D-05: warmup = T x teach_persona.WARMUP_STEPS // teach_persona.MAX_STEPS, the v4.0 "
            "shape (10% of T: 20 at T = 200, 80 at T = 800), with cosine decay over the whole T "
            "(src/personacore/training/schedule.py). WARMUP_STEPS = 20 "
            "(scripts/teach_persona.py:1600) is the v4.0 value and is not changed; E3 passes the "
            "T-derived warmup to the run."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('05')}; scripts/teach_persona.py:1599-1600",
    },
    "d05_seam": {
        "value": ("LR", "WARMUP_STEPS", "MAX_STEPS"),
        "derivation": (
            "D-05, 42-RESEARCH Item 3 [A1]: E3 passes the T-derived warmup by rebinding "
            "teach_persona's module globals LR, WARMUP_STEPS and MAX_STEPS for the duration of one "
            "phase25_points.train_stage call, restored in a finally block (precedent "
            "scripts/phase36_probe.py stage_e3, which rebinds MAX_STEPS). The source constants "
            "LR = 3e-4, MAX_STEPS = 200, WARMUP_STEPS = 20 are the v4.0 values and "
            "scripts/teach_persona.py is never edited. Each record proves the take from the "
            "training sidecar's train_config (lr, warmup_steps, max_steps) and "
            f"live_mechanism.composed_steps. {_DEFAULT}."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('05')}; 42-RESEARCH Item 3; scripts/phase36_probe.py stage_e3",
    },
    "dp_clip": {
        "value": mitigation_budget.CLIP_NORM,
        "derivation": (
            "D-06: C = mitigation_budget.CLIP_NORM on every noised point, the v4.0 "
            "no-interpolation median rule over the dp_n64 per-record norms of "
            "results/phase25_clip_calibration.json. Declared limit: C was calibrated at dp_n64, "
            "sigma = 0, lr 3e-4, T = 200; at lr = 1e-3 or T = 800 the norm distribution may "
            "differ. Each point publishes clip_bind_count as a descriptive reading, no verdict."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('06')}; results/phase25_clip_calibration.json",
    },
    "controls_follow_v4": {
        "value": types.MappingProxyType(
            {
                "clip_norm": mitigation_budget.CONTROL_CLIP_NORM,
                "varies": ("lr", "max_steps", "warmup_steps"),
            }
        ),
        "derivation": (
            "D-07: the 3 new sigma = 0 controls use mitigation_budget.CONTROL_CLIP_NORM "
            "(non-binding, proved clip_bind_count == 0 before scoring by "
            "phase25_points.train_stage) and every train_config field equal to the v4.0 control "
            "record's training.train_config except lr, max_steps and warmup_steps. Declared "
            "limit: the control-to-point gap mixes the per-record clip and the noise; E3 does not "
            "separate the two, as v4.0 did not."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('07')}; {V4_CONTROL_RECORD} training.train_config",
    },
    "p22_check": {
        "value": STEPS,
        "derivation": (
            "RECIPE-04, D-08: phase35_prereg.p22_onset_sigma for every T used, inside the grid "
            "fill at every import of this file, and re-asserted by the driver before any stage-2 "
            "training, each onset equal to P22_ONSETS. Measured onsets 0.0789 (T = 200) and "
            "0.1578 (T = 800); both noised sigma clear them, and the check still runs and is "
            "recorded."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('08')}; scripts/phase35_prereg.py p22_onset_sigma",
    },
    "e3_hours": {
        "value": types.MappingProxyType(
            {"priced_hours": _PRICED_HOURS, "e3_line_hours": _BUDGET["front_hours"]["E3"]}
        ),
        "derivation": (
            "D-09: the priced hours are 5 x price(T = 200) + 6 x price(T = 800), price(T) = "
            "(e3_overhead_high + T x e3_per_step_high + e3_score_high) / 3600 from the budget's "
            "unit_prices, the run counts derived from RECIPES x E3_SIGMAS minus the reused v4.0 "
            "control; no fifth recipe, the slack kept as margin. Expected ceiling: about 5.58 h "
            "(the v4.0 sigma = 1 point scored in 1456.7 s in results/phase25_recall.json against "
            "e3_score_high 1270.6 s, over the 4 sigma = 1 runs) and about 6.23 h with retention "
            "measured (87-213 s per unit, scripts/phase25_condition_c.py docstring, 42-RESEARCH "
            "Item 8), both under the E3 line and far under stop (a)."
        ),
        "kind": "derived",
        "source": (
            f"{_CONTEXT.format('09')}; {BUDGET_RECORD} unit_prices, front_hours.E3; "
            f"{_RECALL_RECORD}"
        ),
    },
    "shared_noise": {
        "value": "the sigma points of one recipe are not independent replicates",
        "derivation": (
            "D-10: one dedicated torch.Generator seeded once from the run seed "
            "(src/personacore/privacy/dpsgd.py:311-314); every step draws torch.normal(std = "
            "sigma x C) with no sigma branch (:486-500). Measured: sigma = 1 noise is exactly 2x "
            "sigma = 0.5 noise at steps 1-3 (torch.equal), on CPU (42-CONTEXT) and on MPS "
            "(42-RESEARCH Item 1, 72 tensors, 331,776 elements, max diff 0.0). Same-sigma points "
            "of the two lr recipes at the same T draw identical noise, and the first 200 steps of "
            "a T = 800 point draw the T = 200 point's noise. The sigma points of one recipe are "
            "NOT independent replicates and no reading treats them as such."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('10')}; 42-RESEARCH Item 1",
    },
    "vacuous": {
        "value": "biased-coin bound e^ε/(e^ε+1), computed per point as 1 / (1 + exp(-ε))",
        "derivation": (
            "D-11: vacuous is by construction, no new cut line. Primary: the biased-coin bound of "
            ".planning/research/V6-PREREG-09.md:53: under ε-DP no guesser beats probability "
            "e^ε/(e^ε+1), computed per point as 1 / (1 + exp(-ε)) in float64 (1.0 at the "
            "smallest grid ε 159.44). 3 distinct ε values (T = 200: 519.70 / 159.44; T = 800: "
            "1840.30 / 519.70; sigma 0.5 at T = 200 and sigma 1 at T = 800 share mu = "
            "sqrt(T)/sigma). Secondary, worded as a rearrangement, never a quotation: with FPR = "
            "P_FA and TPR = 1 − P_MD, the second inequality of Kairouz, Oh and Viswanath, The "
            "Composition Theorem for Differential Privacy (ICML 2015, arXiv:1311.0776v4) "
            "Theorem 2.1 rearranges to TPR ≤ e^ε·FPR + δ. It is vacuous only for FPR ≥ "
            "(1−δ)e^−ε (5.69e-70 at ε = 159.44), and at FPR = 0 it still bounds TPR ≤ δ, so it is "
            "not vacuous for every test."
        ),
        "kind": "preference",
        "source": (
            f"{_CONTEXT.format('11')}; .planning/research/V6-PREREG-09.md:53; 42-RESEARCH "
            "Item 2 (arXiv:1311.0776v4 §2, p. 3)"
        ),
    },
    "point_rule": {
        "value": "taught k/n >= threshold taught AND held-out k/n >= threshold held-out",
        "derivation": (
            "RECIPE-03, D-12: a noised point passes iff taught k/n >= the threshold fill's taught "
            "value AND held-out k/n >= its held-out value, the fill's float read from "
            "E3_RECALL_THRESHOLD, never recomputed (the fill computes F_Y x tk / tn; F_Y = 0.7 "
            "from scripts/mitigation_gate.py:203). A recipe whose threshold is "
            "phase29_prereg.REFUSED has its points labelled REFUSED. The published table is 4 x 2 "
            "(recipe x noised sigma), each cell passa / não passa / REFUSED. The float "
            "comparison is pre-registered and every k where it disagrees with the exact rational "
            "F_Y x tk / tn is enumerated and published (42-RESEARCH Pitfall 6)."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('12')}; scripts/mitigation_gate.py:203",
    },
    "descriptive_readings": {
        "value": ("retention_ppl", "dialogue_gap", "clip_bind_count", "training_seconds"),
        "derivation": (
            "D-13: retention (phase25_condition_c.measure_condition_c retention_ppl with "
            "retention_total_tokens), the dialogue gap (training ppl_adapter_on − "
            "ppl_adapter_off), clip_bind_count and the training seconds are published per unit, "
            "controls and points, as descriptive readings and never enter the label. Each "
            "control's retention is published beside its recipe's points next to the reused v4.0 "
            "control's condition_c.point_retention_ppl (D-18). RECIPE-03 asks only about recall; "
            "the v4.0 retention cap 3.9085 fails intact adapters (41-CONTEXT D-14: Phase 40's "
            "intact adapters read 4.156-4.332)."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('13')}; 41-CONTEXT D-14",
    },
    "summary_and_composition": {
        "value": "k de N pontos passam; m REFUSED",
        "derivation": (
            "RECIPE-02, D-14: the summary line is always the whole count, k de N pontos passam; "
            "m REFUSED, with N the number of noised cells, never a bare sim/não. A yes in 1 of N "
            "is a selection inside the grid and selection_accounted stays "
            "phase35_prereg.SELECTION_ACCOUNTED (False). Each point publishes ε = "
            "phase25_epsilon.point_epsilon_for_sigma(sigma, steps=T, delta=phase35_prereg.DELTA) "
            "at δ = 1e-5 beside basic composition phase35_prereg.CURVE_TOTAL over the noised "
            "points only (the sigma = 0 controls carry no ε) (PREREG-09 §3(b); phase35_prereg "
            "ENTRIES e3_composition / e3_selection_accounted)."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('14')}; .planning/research/V6-PREREG-09.md §3(b)",
    },
    "null_line": {
        "value": (
            "nenhuma receita manteve o recall onde a garantia é vazia "
            f"(0 de {_NOISED_CELLS} pontos)"
        ),
        "derivation": (
            "D-15: if no point passes, the report's FIRST line is, literally, this value, with N "
            "the number of noised cells, followed by every point's raw recall on both legs and "
            "its ε; no ainda, no possivelmente com outra receita, no extrapolation beyond the 4 "
            "recipes and seed 1337."
        ),
        "kind": "preference",
        "source": _CONTEXT.format("15"),
    },
    "predictions": {
        "value": types.MappingProxyType(
            {
                "d16_v4_recipe_points": (
                    "the sigma = 0.5 and sigma = 1 points of the v4.0 recipe repeat the v4.0 "
                    f"recall, {_D16_READINGS} (read from {_RECALL_RECORD}; the point records "
                    "carry no recall fields); the report puts the two readings side by side; "
                    "descriptive; a mismatch is a finding, not a failure"
                ),
                "d17_no_recipe_passes": (
                    "none of the 4 recipes passes the threshold at sigma = 0.5 or sigma = 1; if "
                    "one does it is expected at T = 800, not at lr = 1e-3: under AdamW (the DP "
                    "optimizer, dpsgd.py:32) lr scales signal and noise together and only T "
                    "accumulates signal faster than noise; an argument, not a project "
                    "measurement; descriptive; a mismatch is a finding, not a failure"
                ),
            }
        ),
        "derivation": (
            "D-16, D-17: recorded before any run. D-16's readings are built at import from "
            f"{_RECALL_RECORD} points[phase25_record.point_key(dp_n<E3_N>, sigma)]."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('16, D-17')}; {_RECALL_RECORD}",
    },
    "lr_control_outcome": {
        "value": "REFUSED only via phase29_prereg.control_is_unlearnable",
        "derivation": (
            "D-18 as corrected by Rafael's ruling of 2026-10-13: a sigma = 0 control at lr = 1e-3 "
            "may fail to learn; its recipe's points are then REFUSED, only via "
            "phase29_prereg.control_is_unlearnable, exactly as in v4.0 (the rule reads recall "
            "counts only, scripts/phase29_prereg.py:190-200), reported with the same weight. A "
            "control that learns but degrades retention changes no label: its retention is "
            "published descriptively beside its recipe's points and named in the report with the "
            "same weight. The earlier wording that a retention drop made the points REFUSED was "
            "wrong (v4.0 has no retention leg in REFUSED)."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('18')}; {_RULING_CONTEXT.format('18')}",
    },
    "stages": {
        "value": ("stage 1: the sigma = 0 controls", "stage 2: the noised points"),
        "derivation": (
            "D-19: stage 1 = the 3 new sigma = 0 controls plus the reused v4.0 control's SHA-256 "
            "check (at prereg import); then the stage-1 records are committed and "
            "e3_recall_threshold is filled and committed in scripts/phase42_threshold_prereg.py; "
            "stage 2 = the 8 noised points, P22 re-asserted before any training. The ancestry "
            "tests prove the threshold file precedes the first noised-point record."
        ),
        "kind": "preference",
        "source": _CONTEXT.format("19"),
    },
    "refused_still_run": {
        "value": "a REFUSED recipe's noised points still run",
        "derivation": (
            "D-20: a recipe whose control is unlearnable still runs its noised points, as v4.0 "
            "did for n64; they publish ε and raw recall on both legs, labelled REFUSED. Labels "
            "are applied at emit, never at launch; their cost is inside the priced hours."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('20')}; results/phase25_point_dp_n64_sigma*",
    },
    "rehearsal": {
        "value": (
            "the v4.0 control's SHA-256 reuse",
            "the T-derived warmup",
            "the P22 check for T = 800",
            "the REFUSED path of a control that does not learn",
        ),
        "derivation": (
            "D-21: before any MPS run, a code review of the prereg and the driver, then a short "
            "CPU rehearsal exercising the v4.0 control's SHA-256 reuse, the T-derived warmup (20 "
            "at T = 200, 80 at T = 800), the P22 check for T = 800 and the REFUSED path of a "
            "control that does not learn (Phase 41 precedent: rehearsal 41-11 found a real "
            "defect, fixed in 075f5ea)."
        ),
        "kind": "preference",
        "source": _CONTEXT.format("21"),
    },
    "approvals": {
        "value": "one approved per launch; stage-2 records under three",
        "derivation": (
            "D-22: every commit write-once, each alone, explicit paths; one approved per launch "
            "(stage 1, stage 2); the stage-1 records and the filled threshold under one approved; "
            "the stage-2 records under three (ledger + point records, the E3 record, the report); "
            'launch through phase36_ledger.require_launch("E3") (E3 in V6_MPS_FRONTS; MPS fp32).'
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('22')}; scripts/phase36_ledger.py require_launch",
    },
    "refusal_omitted": {
        "value": "the v4.0 extraction-draw refusal leg is not produced",
        "derivation": (
            "D-13, RECIPE-01..04: the v4.0 extraction-draw refusal leg (about 80 min per point, "
            "phase25_points refusal over attack draws) is not produced: no RECIPE requirement nor "
            "D-13 asks for it and it is unpriced in the E3 unit price. The omission is declared "
            "here and in the report."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('13')}; {_RULING}",
    },
    "own_control_recall": {
        "value": "each noised point publishes its own recipe's control raw recall k/n",
        "derivation": (
            "D-23 (Rafael 2026-10-13): beside its label every noised point publishes the raw "
            "recall k/n of its own recipe's sigma = 0 control on both legs (the reused v4.0 "
            "control's for the v4.0 recipe), in the E3 record and the report table, so a passa "
            "against a control that learned little stays visible. The imported rule (D-12) does "
            "not change."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('12')}; {_RULING_CONTEXT.format('23')}",
    },
    "record_layout": {
        "value": (
            "results/phase42_control_<recipe tag>.json",
            "results/phase42_point_<recipe tag>_<sigma tag>.json",
            "results/phase42_recipes.json",
            "results/phase42_recipes_report.md",
        ),
        "derivation": (
            "D-19, D-22: controls results/phase42_control_<recipe tag>.json; points "
            "results/phase42_point_<recipe tag>_<sigma tag>.json, never matching CONTROL_GLOB (a "
            "noised record under the control glob would be exempt from leg (a)); the aggregate "
            "results/phase42_recipes.json and the report results/phase42_recipes_report.md; "
            "training prefixes phase42e3_<unit> (real) and phase42rh_<unit> (rehearsal), never "
            f"phase25_ nor phase42_; their run.csv directories gitignored. {_DEFAULT}."
        ),
        "kind": "preference",
        "source": _CONTEXT.format("19, D-22"),
    },
    "unit_order": {
        "value": ("stage 1: controls in RECIPES order", "stage 2: RECIPES x noised sigma"),
        "derivation": (
            "D-19, D-20: stage 1 runs the 3 new controls in RECIPES order; stage 2 runs the 8 "
            f"noised points in RECIPES x noised-sigma order, REFUSED recipes included. {_DEFAULT}."
        ),
        "kind": "preference",
        "source": _CONTEXT.format("19, D-20"),
    },
    "crash_rule": {
        "value": "reconcile lost, relaunch only after Rafael's approved",
        "derivation": (
            "D-22: a unit without its record and with an open ledger attempt is reconciled lost "
            "by phase36_ledger reconcile; a unit record written with its attempt open gets its "
            "end line by command, never a reconcile; a relaunch runs only after Rafael's approved "
            "and a cause note, at the same HEAD or an approved fix committed first; "
            "phase25_points.train_stage then resumes from the unit's latest.pt (the checkpoint "
            "carries the DP noise generator state, dp_noise_rng) or reuses a finished sidecar, "
            "after the driver proves the checkpoint's train_config lr / warmup_steps / max_steps "
            "equal the cell's (42-RESEARCH Pitfall 1); the record lists the unit's lost attempts "
            f"from the ledger and its resumed_from_step; partial outputs are kept. {_DEFAULT}."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('22')}; 42-RESEARCH Pitfall 1",
    },
    "rehearsal_shape": {
        "value": "scratch root, CPU with MPS hidden, phase42rh prefix",
        "derivation": (
            "D-21: scratch root, CPU with MPS hidden, phase42rh prefix, its own ledger and "
            "heartbeat. Stage 1 runs the control of recipe (1e-3, 200) for real (warmup 20) and "
            "the two T = 800 controls through the driver's real writer with the trainer and "
            "scorer seams stood in, one stand-in unlearnable (0 taught, 0 held-out) to exercise "
            "REFUSED; the real threshold fill on the scratch root. Stage 2 runs the point (3e-4, "
            "800, sigma = 1) for real (warmup 80, the real DP noise, ε at T = 800) and the other 7 "
            "points with stand-in seams; a planted P22 crossing at T = 800 refuses before any "
            "training; a tampered copy of the v4.0 control refuses the threshold fill; emit and "
            f"report on the scratch root. {_DEFAULT}."
        ),
        "kind": "preference",
        "source": _CONTEXT.format("21"),
    },
}

ENTRIES = types.MappingProxyType(
    {name: types.MappingProxyType(entry) for name, entry in _ENTRIES.items()}
)

_ENTRY_NAMES = frozenset(
    {
        "e3_grid_subset",
        "batch_and_q",
        "v4_control_reuse",
        "one_seed",
        "warmup_rule",
        "d05_seam",
        "dp_clip",
        "controls_follow_v4",
        "p22_check",
        "e3_hours",
        "shared_noise",
        "vacuous",
        "point_rule",
        "descriptive_readings",
        "summary_and_composition",
        "null_line",
        "predictions",
        "lr_control_outcome",
        "stages",
        "refused_still_run",
        "rehearsal",
        "approvals",
        "refusal_omitted",
        "own_control_recall",
        "record_layout",
        "unit_order",
        "crash_rule",
        "rehearsal_shape",
    }
)


def _prove_entries():
    """Every entry proved, and the entry set exactly the pre-registered names."""
    for name, entry in ENTRIES.items():
        _prove_entry(name, entry)
    _prove(
        set(ENTRIES) == _ENTRY_NAMES,
        f"entries {sorted(set(ENTRIES) ^ _ENTRY_NAMES)} are missing or extra",
    )


_prove_entries()

# =================================================================================================
# (6) THE SLOT FILL: once, the whole value of its module-level binding. The one Phase 42 slot with
# no in-phase input, so leg (a) puts this file before every results/phase42_* record. The rule
# checks the v4.0 control against tag v5.0 and P22 for every T used (RECIPE-04, D-08).
# =================================================================================================

E3_GRID_SUBSET = phase35_prereg.fill(
    "e3_grid_subset",
    recipes=RECIPES,
    seed=SEED,
    input_records=(BUDGET_RECORD, V4_CONTROL_RECORD),
    derivation=ENTRIES["e3_grid_subset"],
)

# The grid's counts and its sigma count against the committed caps (unit_caps.E3).
phase36_caps.check_unit_caps("E3", **phase36_caps.counts_for("e3_grid_subset", E3_GRID_SUBSET))
phase36_caps.check_unit_caps("E3", sigmas=len(phase35_prereg.E3_SIGMAS))

# D-09: the priced runs are exactly the fill's non-reused cells.
_prove(
    tuple(c["recipe"]["steps"] for c in E3_GRID_SUBSET["cells"] if c["reuse"] is None)
    == _TRAINED_STEPS,
    "the priced runs are not the grid's non-reused cells",
)

# D-08: the onsets the rule computed, re-asserted by the driver before any stage-2 training.
P22_ONSETS = E3_GRID_SUBSET["p22_onset_sigma"]

# =================================================================================================
# (7) THE UNITS AND WHERE THEY WRITE (D-19, D-20, D-22; record_layout, unit_order). A unit is one
# ledger attempt: a new sigma = 0 control (stage 1) or a noised point (stage 2). Every name, path,
# run id and training prefix below is a function of the grid; the driver computes nothing beyond.
# =================================================================================================


def recipe_tag(recipe):
    """``lr<lr:.0e>_t<steps>`` of a grid recipe (``lr3e-04_t200``); refuses a recipe outside
    RECIPES."""
    _prove(recipe in RECIPES, f"recipe {recipe!r} is not one of RECIPES")
    return f"lr{recipe['lr']:.0e}_t{recipe['steps']}"


def sigma_tag(sigma):
    """The sigma suffix of ``phase25_record.point_key(dp_n<E3_N>, sigma)`` (``sigma0p500000``),
    read, never formatted here; refuses a sigma outside phase35_prereg.E3_SIGMAS."""
    _prove(sigma in phase35_prereg.E3_SIGMAS, f"sigma {sigma!r} is not one of E3_SIGMAS")
    arm = f"dp_n{phase35_prereg.E3_N}_"
    key = phase25_record.point_key(arm[:-1], sigma)
    _prove(key.startswith(arm), f"point key {key!r} does not start with {arm!r}")
    return key.removeprefix(arm)


# D-03: the recipe whose sigma = 0 cell reuses the v4.0 control, read from the fill.
_REUSED = tuple(c["recipe"] for c in E3_GRID_SUBSET["cells"] if c["reuse"] is not None)
_prove(len(_REUSED) == 1, f"the grid reuses {len(_REUSED)} cells, not exactly one")
(REUSED_RECIPE,) = _REUSED

# unit_order: stage 1 the new controls in RECIPES order, stage 2 RECIPES x NOISED_SIGMAS (a REFUSED
# recipe's points included, D-20).
_CONTROL_CELLS = {
    f"control_{recipe_tag(r)}": (r, CONTROL_SIGMA) for r in RECIPES if r != REUSED_RECIPE
}
_POINT_CELLS = {
    f"point_{recipe_tag(r)}_{sigma_tag(s)}": (r, s) for r in RECIPES for s in NOISED_SIGMAS
}
CONTROL_UNITS = tuple(_CONTROL_CELLS)
POINT_UNITS = tuple(_POINT_CELLS)
UNITS = CONTROL_UNITS + POINT_UNITS
_UNIT_CELLS = types.MappingProxyType({**_CONTROL_CELLS, **_POINT_CELLS})
_prove(tuple(_UNIT_CELLS) == UNITS, "the units are not distinct")


def unit_cell(unit):
    """``(recipe, sigma)`` of the grid cell a unit names; refuses a name outside UNITS."""
    _prove(isinstance(unit, str) and unit in _UNIT_CELLS, f"unit {unit!r} is not one of UNITS")
    return _UNIT_CELLS[unit]


def unit_record(unit):
    """record_layout / D-22: a control's record under CONTROL_GLOB, a point's under RECORD_GLOB and
    never under CONTROL_GLOB (a noised record there would be exempt from leg (a), 42-RESEARCH
    Pitfall 10)."""
    recipe, sigma = unit_cell(unit)
    if sigma == CONTROL_SIGMA:
        path = CONTROL_GLOB.replace("*", recipe_tag(recipe))
        _prove(fnmatch.fnmatch(path, CONTROL_GLOB), f"{path} does not match {CONTROL_GLOB}")
        return path
    path = RECORD_GLOB.replace("*", f"{unit}.json")
    _prove(fnmatch.fnmatch(path, RECORD_GLOB), f"{path} does not match {RECORD_GLOB}")
    _prove(not fnmatch.fnmatch(path, CONTROL_GLOB), f"point {path} would read as a control record")
    return path


E3_RECORD = RECORD_GLOB.replace("*", "recipes.json")
REPORT_RECORD = RECORD_GLOB.replace("*", "recipes_report.md")


def run_id(unit):
    """The ledger run id of one Phase 42 unit on front E3."""
    import phase36_ledger  # torch-free; lazy so the import surface stays small

    _prove(unit in UNITS, f"unit {unit!r} is not one of UNITS")
    return phase36_ledger.run_id(42, "E3", unit)


# Neither prefix matches results/phase42_* (the record glob): the run.csv directories they name
# are gitignored (precedent phase41rh).
REAL_PREFIX = "phase42e3"
REHEARSAL_PREFIX = "phase42rh"


def train_prefix(unit, *, rehearsal):
    """The teach_persona.arm_outputs prefix of one unit: ``phase42e3_<unit>`` for the real run,
    ``phase42rh_<unit>`` for the CPU rehearsal; never ``phase25_*`` nor ``phase42_*``."""
    _prove(unit in UNITS, f"unit {unit!r} is not one of UNITS")
    prefix = f"{REHEARSAL_PREFIX if rehearsal else REAL_PREFIX}_{unit}"
    _prove(
        not prefix.startswith(("phase25_", "phase42_")),
        f"prefix {prefix!r} would write under a record glob",
    )
    return prefix


def warmup_for(steps):
    """D-05: warmup = T x teach_persona.WARMUP_STEPS // teach_persona.MAX_STEPS (the v4.0 shape),
    refused unless exact; teach_persona's constants are read, never edited."""
    _prove(
        steps * teach_persona.WARMUP_STEPS % teach_persona.MAX_STEPS == 0,
        f"warmup for T = {steps} is not an exact fraction of the v4.0 shape",
    )
    return steps * teach_persona.WARMUP_STEPS // teach_persona.MAX_STEPS


_prove(all(warmup_for(t) == w for t, w in WARMUPS.items()), "warmup_for disagrees with WARMUPS")

# =================================================================================================
# (8) THE DRIVER'S TAKE PROOFS (D-05, D-06, D-07) AND THE THRESHOLD FILL'S EXACT KWARGS (RECIPE-03,
# D-12, D-19). This file never calls fill("e3_recall_threshold"): that slot is filled once, in
# scripts/phase42_threshold_prereg.py, after the 3 new controls are committed.
# =================================================================================================


def clip_norm_for(sigma):
    """D-06 / D-07: mitigation_budget.CONTROL_CLIP_NORM (non-binding) at the control sigma,
    mitigation_budget.CLIP_NORM at every noised sigma; refuses any other sigma."""
    if sigma == CONTROL_SIGMA:
        return mitigation_budget.CONTROL_CLIP_NORM
    _prove(sigma in NOISED_SIGMAS, f"sigma {sigma!r} is not one of the grid's sigmas")
    return mitigation_budget.CLIP_NORM


def expected_train_config(recipe):
    """D-05 / D-07: the v4.0 control record's training.train_config with only lr, max_steps and
    warmup_steps replaced by the recipe's; everything else (grad_clip, batch_size,
    grad_accum_steps, seed, weight_decay) is the v4.0 control's. Read-only."""
    _prove(recipe in RECIPES, f"recipe {recipe!r} is not one of RECIPES")
    return types.MappingProxyType(
        dict(
            _V4["training"]["train_config"],
            lr=recipe["lr"],
            max_steps=recipe["steps"],
            warmup_steps=warmup_for(recipe["steps"]),
        )
    )


def recipe_key(recipe):
    """``(lr, steps, batch, SEED)``: the key the Phase 35 threshold rule builds from a record."""
    _prove(recipe in RECIPES, f"recipe {recipe!r} is not one of RECIPES")
    return (recipe["lr"], recipe["steps"], recipe["batch"], SEED)


def threshold_fill_inputs():
    """RECIPE-03 / D-12 / D-19: the exact kwargs of ``phase35_prereg.fill("e3_recall_threshold",
    ...)``: the grid by identity, the reused v4.0 control plus the 3 new control records, and a
    four-field derivation whose value is the tuple of the grid's recipe keys and whose source names
    every input path. A fresh object each call (phase41_prereg.floors_fill_inputs)."""
    input_records = (V4_CONTROL_RECORD,) + tuple(unit_record(u) for u in CONTROL_UNITS)
    derivation = {
        "value": tuple(recipe_key(r) for r in RECIPES),
        "derivation": (
            "RECIPE-03 / D-12 / D-19: the threshold of every grid recipe is F_Y x the recall of "
            "ITS OWN sigma = 0 control on each leg (taught, held-out), never a control borrowed "
            "from another recipe; the v4.0 recipe reuses the v4.0 control (verified "
            "byte-identical to tag v5.0); a control that does not learn "
            "(phase29_prereg.control_is_unlearnable) makes its recipe REFUSED (D-18); filled in "
            "scripts/phase42_threshold_prereg.py after the 3 new controls are committed and "
            "before any noised record"
        ),
        "kind": "derived",
        "source": (
            f"{_CONTEXT.format('12, D-19')}; {_RULING_CONTEXT.format('18')}; "
            + " ".join(input_records)
        ),
    }
    _prove_entry("threshold_fill_inputs", derivation)
    return {"grid": E3_GRID_SUBSET, "input_records": input_records, "derivation": derivation}


# =================================================================================================
# (9) THE ANSWER'S FORM (RECIPE-03; D-12, D-13, D-14, D-15, D-18, D-23): the per-point verdict, the
# 4 x 2 table with each recipe's own control recall beside the labels, the descriptive readings,
# the summary line and the null lead. Written before any record; emit calls these, never computes.
# =================================================================================================

PASSA = "passa"
NAO_PASSA = "não passa"
REFUSED = phase29_prereg.REFUSED
LABELS = (PASSA, NAO_PASSA, REFUSED)


def _rate(pair):
    """``k / n`` of a ``(k, n)`` recall pair of non-bool ints with 0 <= k <= n and n >= 1."""
    _prove(
        isinstance(pair, tuple) and len(pair) == 2,
        f"recall {pair!r} is not a (k, n) tuple",
    )
    k, n = pair
    _prove_count("k", k)
    _prove_count("n", n, low=1)
    _prove(k <= n, f"recall {k}/{n} has k > n")
    return k / n


def point_verdict(taught, heldout, threshold):
    """RECIPE-03 / D-12: PASSA iff taught k/n >= threshold["taught"] AND held-out k/n >=
    threshold["heldout"], the fill's floats used as given (never recomputed); NAO_PASSA otherwise;
    REFUSED whenever the fill's threshold is REFUSED, whatever the counts (REFUSED comes only from
    the fill, i.e. phase29_prereg.control_is_unlearnable; D-18 as corrected 2026-10-13). D-13: the
    arguments are the recall pairs and the threshold, nothing else."""
    taught_rate, heldout_rate = _rate(taught), _rate(heldout)
    if threshold == REFUSED:
        return REFUSED
    if taught_rate >= threshold["taught"] and heldout_rate >= threshold["heldout"]:
        return PASSA
    return NAO_PASSA


def _prove_verdicts(verdicts):
    """Exactly one label from LABELS per POINT_UNITS member."""
    _prove(
        set(verdicts) == set(POINT_UNITS),
        f"verdict units {sorted(set(verdicts) ^ set(POINT_UNITS))} are missing or extra",
    )
    for unit, label in verdicts.items():
        _prove(label in LABELS, f"unit {unit} has label {label!r}, not one of {LABELS}")


def table(verdicts, control_recall):
    """D-12 / D-23: the 4 x 2 table, one row per recipe in RECIPES order: the recipe tag, one cell
    per NOISED_SIGMAS member holding that point's label, and the raw recall k/n of the recipe's own
    sigma = 0 control on both legs (``control_recall`` keyed by recipe tag; the reused v4.0
    control's for the v4.0 recipe). The control counts sit beside the labels and never enter
    them."""
    _prove_verdicts(verdicts)
    tags = {recipe_tag(r) for r in RECIPES}
    _prove(
        set(control_recall) == tags,
        f"control recall recipes {sorted(set(control_recall) ^ tags)} are missing or extra",
    )
    rows = []
    for recipe in RECIPES:
        tag = recipe_tag(recipe)
        row = {"recipe": tag}
        for sigma in NOISED_SIGMAS:
            row[sigma_tag(sigma)] = verdicts[f"point_{tag}_{sigma_tag(sigma)}"]
        for leg in ("taught", "heldout"):
            pair = control_recall[tag][leg]
            _rate(pair)
            row[f"control_{leg}"] = f"{pair[0]}/{pair[1]}"
        rows.append(types.MappingProxyType(row))
    return tuple(rows)


def _field(record, *path):
    """``record[path[0]][path[1]]...``, refused when any key is absent."""
    value = record
    for key in path:
        _prove(
            isinstance(value, collections.abc.Mapping) and key in value,
            f"record has no {'.'.join(path)}",
        )
        value = value[key]
    return value


def descriptive_reading(record):
    """D-13: retention, the dialogue gap, clip_bind_count and the training and scoring seconds of
    one unit record, labelled descriptive; none of them enters a label."""
    return types.MappingProxyType(
        {
            "kind": "descriptive",
            "retention_ppl": _field(record, "condition_c", "retention_ppl"),
            "retention_total_tokens": _field(record, "condition_c", "retention_total_tokens"),
            "dialogue_gap": _field(record, "dialogue_gap"),
            "clip_bind_count": _field(record, "clip_bind_count"),
            "train_seconds": _field(record, "training", "seconds"),
            "scoring_seconds": _field(record, "scoring_seconds"),
        }
    )


# D-18: the reused v4.0 control's retention, read from its record.
V4_CONTROL_RETENTION = _V4["condition_c"]["point_retention_ppl"]


def control_retention_row(recipe, retention_ppl):
    """D-18 (as corrected 2026-10-13): a control's retention beside the reused v4.0 control's and
    their difference, labelled descriptive, with the report's sentence; a retention drop changes
    no label. For REUSED_RECIPE the caller passes V4_CONTROL_RETENTION itself."""
    tag = recipe_tag(recipe)
    return types.MappingProxyType(
        {
            "recipe": tag,
            "retention_ppl": retention_ppl,
            "v4_control_retention_ppl": V4_CONTROL_RETENTION,
            "difference": retention_ppl - V4_CONTROL_RETENTION,
            "kind": "descriptive",
            "text": (
                f"retenção do controle {tag}: {retention_ppl:.4f} (controle v4.0: "
                f"{V4_CONTROL_RETENTION:.4f}); leitura descritiva, não muda rótulo (D-18)"
            ),
        }
    )


def summary_line(verdicts):
    """D-14: always the whole count, "k de N pontos passam; m REFUSED", N = len(POINT_UNITS)."""
    _prove_verdicts(verdicts)
    k = sum(label == PASSA for label in verdicts.values())
    m = sum(label == REFUSED for label in verdicts.values())
    return f"{k} de {len(POINT_UNITS)} pontos passam; {m} REFUSED"


def null_line():
    """D-15: the report's first line when no point passes; equal to ENTRIES["null_line"]."""
    line = (
        f"nenhuma receita manteve o recall onde a garantia é vazia (0 de {len(POINT_UNITS)} pontos)"
    )
    _prove(line == ENTRIES["null_line"]["value"], "null_line disagrees with ENTRIES null_line")
    return line


def report_lead(verdicts):
    """D-15 / D-14: the report's ONE lead line: null_line() when no point passes, else the summary
    line. The report follows it with every point's raw recall and epsilon, and prints the summary
    line once."""
    _prove_verdicts(verdicts)
    if PASSA not in verdicts.values():
        return null_line()
    return summary_line(verdicts)
