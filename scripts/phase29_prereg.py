"""Phase 29 PRE-REGISTRATION — the v5.0 adversarial-with-replay (``advr``) sweep's keys, result
paths, replay recipe, gate route and own-control refusal, committed before any v5.0 number exists.

WHAT THIS FREEZES. The 12 point keys (D-01) rendered by WRAPPING ``phase25_record.point_key``
(never editing it) under the ``advr`` arms; every v5.0 results path in ONE tuple,
``V5_RESULT_PATHS`` (D-02), with the ancestry pathspecs DERIVED from it (D-03); the replay recipe
as the DP arms' own expression, imported lazily (D-04); the gate route, ``F_Y`` and the ratio grid
BY REFERENCE (D-05); the unlearnable-own-control refusal predicate and the REFUSED record shape
(D-11..D-13); the complete key set with no retry/alternate surface (D-14); and the named
limitations (D-19 DEBT-04, D-17 TD-16-R1). Added by Plan 29-04, AFTER the developer's GATE-08
ruling (CONTEXT D-15, option 2 — no promotion): the D-09 relearning pins, the admission contract
with its CANDIDATE-UNREPLICATED reading, and the scope rule (D-06..D-10, PREREG-02).

``ADVR_ARMS`` IS THE SEAM. Phase 30 imports it from here. It must NEVER be appended to
``teach_persona.ADV_ARMS``: ``phase25_verdict.curve_verdicts`` would then find a key matching two
legs and refuse. The v4.0 parsers (``phase25_record.parse_point_key``,
``phase27_prereg.arm_of``) refuse every ``advr_*`` key, which is what keeps a v4.0 DP reading
from ever being read as a v5.0 control (WR-05).

ANCESTRY-GUARDED. ``tests/test_phase29_prereg.py``
(``test_phase29_prereg_is_frozen_before_every_v5_result``) requires EVERY commit touching this
file to be a strict ancestor of the first-add of every tracked file matched by
``ARTIFACT_PATHSPECS`` (``results/phase30_*`` .. ``results/phase34_*``). After Phase 30's first
results commit, a correction goes through ``scripts/_addendum.py`` as a dated continuation — never
an edit here.

CPU-ONLY AT IMPORT. Stdlib + sibling scripts only. ``teach_persona`` (torch at import) is imported
LAZILY inside ``replay_windows``. ``personacore.privacy.accountant`` IS loaded, TRANSITIVELY, via
``phase25_record`` -> ``phase25_epsilon``; that load is unavoidable and stated rather than hidden.
No v5.0 code path calls it (D-19) — the AST census in the test file enforces it over every
``scripts/phase29_*`` .. ``phase34_*`` module.

THE ROUTE, NEVER THE PIN. Verdicts go through ``phase20_gate_coverage.corrected_point_verdict``
(``GATE_ROUTE``). The frozen pin in ``mitigation_gate`` is never imported or named here
(``tests/test_phase20_correction.py``'s caller census).

Threats mitigated: T-29-01 (post-hoc re-tune — ancestry guard over derived pathspecs); T-29-02
(retry after a refused control — 12 write-once keys, no retry surface); T-29-03 (path traversal —
keys inherit ``phase25_record.point_key``'s refusals and paths are proved against the key set);
T-29-04 (DP floor spoofing an ``advr`` control — ``advr``-keyed controls, v4.0 parsers refuse
them); T-29-05 (re-typed constants — ``is`` tests + AST guards); T-29-06 (an ε leaking into a
v5.0 number — accountant census).
"""

import math
import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import mitigation_budget  # noqa: E402  (needs the sys.path insert above)
import mitigation_gate  # noqa: E402  (same)
import phase20_gate_coverage  # noqa: E402  (same)
import phase25_promotion  # noqa: E402  (same)
import phase25_record  # noqa: E402  (same)
import phase27_prereg  # noqa: E402  (same; torch-free, measured)

# =================================================================================================
# (1) THE DATE AND THE PROPERTY IT CERTIFIES.
# =================================================================================================

# At this commit no `results/phase3[0-4]_*` file existed, tracked or untracked.
COMMITTED = "2026-09-24"
RECORDS_AT_COMMIT = 0


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase29_prereg] {message}")


def _prove_count(name, value):
    """``prove_reproduction``'s register: an ``int`` that is not a ``bool``, or a refusal."""
    _prove(
        isinstance(value, int) and not isinstance(value, bool),
        f"{name} is {value!r}, which is not an int (bool excluded). This formula takes COUNTS; a "
        "float came out of arithmetic and a bool would compare True against 1",
    )


# =================================================================================================
# (2) BY REFERENCE, NEVER RETYPED (D-05) — the test file asserts identity (`is`).
# =================================================================================================

RATIO_GRID = mitigation_budget.ADVERSARIAL_RATIO_GRID
F_Y = mitigation_gate.F_Y
GATE_ROUTE = phase20_gate_coverage.corrected_point_verdict
COVERAGE_FLOOR_REFUSAL_MARKERS = phase25_promotion.COVERAGE_FLOOR_REFUSAL_MARKERS

# =================================================================================================
# (3) THE KEYS (D-01, D-14).
# =================================================================================================

# Imported by Phase 30; never appended to teach_persona.ADV_ARMS (see the module docstring).
ADVR_ARMS = ("advr_n8", "advr_n64")
_V4_TWIN = {"advr_n8": "adv_n8", "advr_n64": "adv_n64"}
LEGS = ("n8", "n64")


def point_key(arm, ratio):
    """``advr_*`` key: the v4.0 twin's rendering with the arm swapped. Inherits every refusal."""
    _prove(arm in ADVR_ARMS, f"arm {arm!r} is not one of the v5.0 arms {ADVR_ARMS}")
    twin = _V4_TWIN[arm]
    return arm + phase25_record.point_key(twin, ratio)[len(twin) :]


def POINT_KEYS():
    """The complete 12-key tuple, arm-major, each leg's ratio-0 control first (ACTRL-02).

    A FUNCTION, like ``phase25_record.ORDERED_POINT_KEYS``: resolved at call, never at import.
    """
    return tuple(point_key(arm, ratio) for arm in ADVR_ARMS for ratio in RATIO_GRID)


def control_key(leg):
    """The leg's own ratio-0 ``advr`` control — never a ``dp_*`` reading (WR-05)."""
    _prove(leg in LEGS, f"leg {leg!r} is not one of {LEGS}")
    return point_key(f"advr_{leg}", RATIO_GRID[0])


def leg_keys(leg):
    """D-12's short-circuit set: every key of ``leg``, control first, DERIVED from POINT_KEYS().

    A refused control means every key here gets a REFUSED record and none is trained.
    """
    _prove(leg in LEGS, f"leg {leg!r} is not one of {LEGS}")
    return tuple(k for k in POINT_KEYS() if k.startswith(f"advr_{leg}_"))


# =================================================================================================
# (4) THE PATHS (D-02, D-03). Later phases import these names; they never retype them.
# =================================================================================================

POINT_RECORD_PREFIX = "results/phase32_point_"


def point_record_path(key):
    """``results/phase32_point_<key>.json`` for one of the 12 keys, refused otherwise."""
    _prove(key in POINT_KEYS(), f"{key!r} is not one of the 12 pre-registered v5.0 keys")
    return f"{POINT_RECORD_PREFIX}{key}.json"


V5_RESULT_PATHS = (
    "results/phase30_calibration.json",  # ARECIPE-02
    "results/phase31_probe_point.json",  # ARCAL-01
    "results/phase31_probe_relearn.json",  # ARCAL-02
    "results/phase31_budget.json",  # ARCAL-03
    POINT_RECORD_PREFIX + "*.json",  # AFRONT-01
    "results/phase32_frontier.json",  # AFRONT-02
    "results/phase33_admission.json",  # ADMIT-02
    "results/phase33_*",  # RELRN-06..09 legs
    "results/phase34_*",  # RPT-04
)

# DERIVED, not typed: exactly results/phase30_* .. results/phase34_*.
ARTIFACT_PATHSPECS = tuple(sorted({p.split("_", 1)[0] + "_*" for p in V5_RESULT_PATHS}))

# =================================================================================================
# (5) THE REPLAY RECIPE (D-04, PREREG-04) — the DP arms' expression, imported lazily.
# =================================================================================================

# Names, not paths: resolved against teach_persona at use.
REPLAY_SOURCE = ("teach_persona.DIALOG_TRAIN_BIN", "teach_persona.DIALOG_TRAIN_MASK")


def replay_windows(n_facts):
    """Replay WINDOWS for ``n_facts``: teach_persona.py's DP call-site expression, by call."""
    import teach_persona  # torch at import — lazy, so this module stays CPU-only

    _prove_count("n_facts", n_facts)
    _prove(n_facts > 0, f"n_facts {n_facts} is not positive")
    windows = teach_persona.replay_window_budget(n_facts) // teach_persona.BLOCK_SIZE
    _prove(
        windows == teach_persona.REPLAY_WINDOWS_PER_FACT * int(n_facts),
        f"replay windows {windows} disagree with REPLAY_WINDOWS_PER_FACT * n_facts",
    )
    return windows


# =================================================================================================
# (6) THE UNLEARNABLE-OWN-CONTROL REFUSAL (D-11..D-13, PREREG-03).
# =================================================================================================


def control_is_unlearnable(taught_k, taught_n, heldout_k, heldout_n):
    """True iff the route's floor precondition (phase20_gate_coverage.py:641-647) fails.

    The same inequality, ``0.0 < F_Y * recall <= 1.0`` on both legs, evaluated on COUNTS.
    """
    pairs = ((taught_k, taught_n), (heldout_k, heldout_n))
    for name, (k, n) in zip(("taught", "heldout"), pairs):
        _prove_count(f"{name}_k", k)
        _prove_count(f"{name}_n", n)
        _prove(0 <= k <= n and n > 0, f"{name} recall {k}/{n} is not a count out of n > 0")
    return not all(0.0 < F_Y * (k / n) <= 1.0 for k, n in pairs)


# A pinned reading, re-read from the frontier by a test; never loaded at import.
V4_ADV_N64_READING = {
    "taught": (1, 1008),
    "heldout": (0, 648),
    "source": "results/phase25_frontier.json::verdicts.control_readings.adv_n64.recall_counts",
}

REFUSED_RECORD_FIELDS = (
    "point_key",
    "control_key",
    "control_recall_counts",
    "recipe",
    "v4_adv_n64_reading",
    "rule",
)
_RECIPE_FIELDS = frozenset(("replay_windows", "n_facts", "seed", "max_steps"))


def _prove_pair(name, pair):
    _prove(
        isinstance(pair, (tuple, list)) and len(pair) == 2,
        f"{name} {pair!r} is not a (k, n) count pair",
    )
    for part in pair:
        _prove_count(name, part)


def refused_record(key, *, taught, heldout, recipe):
    """The REFUSED record for ``key`` (D-12, D-13). Builds the dict; writes nothing.

    Phase 32 writes it, write-once. Refuses unless the control reading is genuinely unlearnable.
    """
    _prove(key in POINT_KEYS(), f"{key!r} is not one of the 12 pre-registered v5.0 keys")
    _prove_pair("taught", taught)
    _prove_pair("heldout", heldout)
    _prove(
        control_is_unlearnable(*taught, *heldout),
        f"control recall taught {taught} / heldout {heldout} is learnable; nothing to refuse",
    )
    _prove(
        isinstance(recipe, dict) and set(recipe) == _RECIPE_FIELDS,
        f"recipe keys {sorted(recipe) if isinstance(recipe, dict) else recipe!r} are not "
        f"{sorted(_RECIPE_FIELDS)}",
    )
    leg = next(leg for leg in LEGS if key in leg_keys(leg))
    # D-13 recipe identity, checked against the key's leg: n and the D-04 replay expression are
    # pinned here; seed and max_steps are Phase 30's calibration (ARECIPE-02), so only their type.
    n = int(leg.removeprefix("n"))
    for field in sorted(_RECIPE_FIELDS):
        _prove_count(f"recipe {field}", recipe[field])
    _prove(recipe["n_facts"] == n, f"recipe n_facts {recipe['n_facts']} != leg {leg}'s {n}")
    _prove(
        recipe["replay_windows"] == replay_windows(n),
        f"recipe replay_windows {recipe['replay_windows']} is not the D-04 expression for n={n}",
    )
    _prove(recipe["seed"] >= 0, f"recipe seed {recipe['seed']} is negative")
    _prove(recipe["max_steps"] > 0, f"recipe max_steps {recipe['max_steps']} is not positive")
    return {
        "point_key": key,
        "control_key": control_key(leg),
        "control_recall_counts": {"taught": list(taught), "heldout": list(heldout)},
        "recipe": dict(recipe),
        "v4_adv_n64_reading": V4_ADV_N64_READING,
        "rule": "PREREG-03",
    }


# =================================================================================================
# (7) NAMED LIMITATIONS (D-19 DEBT-04, D-17 DEBT-02).
# =================================================================================================

NAMED_LIMITATIONS = {
    "P22-WARNING-4/5": {
        "reason": (
            "no v5.0 number uses the accountant; the adversarial arm carries no ε claim "
            "(Phase 25 D-01)"
        ),
        "source": (
            ".planning/milestones/v4.0-phases/"
            "22-dp-sgd-core-accountant-and-the-correctness-battery/22-VERIFICATION.md:149-183"
        ),
        "ledger_rows": ("P22-WARNING-4", "P22-WARNING-5"),
        "transitive_load": (
            "personacore.privacy.accountant is loaded transitively via phase25_record -> "
            "phase25_epsilon; no v5.0 module imports or calls it (AST census in "
            "tests/test_phase29_prereg.py)"
        ),
    },
    "TD-16-R1-REPORT": {
        "reason": (
            "the D-28 READING QUALIFICATION's verbatim kernel is absent from the published "
            "results/phase16_persistence_report.md; the published bytes are kept (D-17) and the "
            "note is read at runtime by phase16_persistence.d28_note()"
        ),
        "ledger_rows": ("TD-16-R1",),
    },
    "GATE-08-NO-PROMOTION": {
        "reason": (
            "D-15 ruled option 2 (29-04 checkpoint, 2026-09-24): no promotion is pre-registered. "
            "A point clearing (a)(b)(c) stays the gate's replication-pending INCONCLUSIVE and the "
            "admission reads CANDIDATE-UNREPLICATED; RELRN-06..09 then ship as a named limitation"
        ),
        "ruling": ".planning/phases/29-v5-0-pre-registration-and-carried-debt/29-04-SUMMARY.md",
    },
}


# =================================================================================================
# (8) THE D-09 RELEARNING PINS — by reference to phase27_prereg, never retyped. The test file
#     checks each binding in the AST (``is`` alone is vacuous on CPython's small-int cache).
# =================================================================================================

MARGIN_K = phase27_prereg.MARGIN_K
CURVE_K = phase27_prereg.CURVE_K
FULL_K = phase27_prereg.FULL_K
RUNGS = phase27_prereg.RUNGS
RELEARN_CAP = phase27_prereg.RELEARN_CAP
MAX_STEPS = phase27_prereg.MAX_STEPS
CHECKPOINT_INTERVAL = phase27_prereg.CHECKPOINT_INTERVAL
DESIGNATED_SEED = phase27_prereg.DESIGNATED_SEED
FRESH_SEEDS = phase27_prereg.FRESH_SEEDS
POOLED_SEED_INDEX = phase27_prereg.POOLED_SEED_INDEX
ATTACKER_CORPUS = phase27_prereg.ATTACKER_CORPUS
first_clear = phase27_prereg.first_clear
z_rule = phase27_prereg.z_rule
band = phase27_prereg.band
recovery_gate = phase27_prereg.recovery_gate
promote_at_z = phase27_prereg.promote_at_z
point_verdict_string = phase27_prereg.point_verdict_string
cleared_abc = phase27_prereg.cleared_abc
REFUSED = phase27_prereg.REFUSED
V4_VERDICTS = mitigation_gate.V4_VERDICTS

# D-09 (b), accepted: only the five never-taught baselines. control_n8/control_n64 in
# phase27_prereg are DP sigma=0 adapters and never become an advr baseline (WR-05).
NEVER_TAUGHT_BASELINES = {
    k: v for k, v in phase27_prereg.PINNED_BASELINES.items() if k.split("_")[0] == "never"
}
# The advr relearning control, pinned by Phase-32 RECORD reference: its digest cannot exist yet.
CONTROL_BASELINE_SOURCE = POINT_RECORD_PREFIX + "{control_key}.json::adapter_sha256"


def control_baseline_source(leg):
    """``results/phase32_point_<control_key(leg)>.json::adapter_sha256`` — the advr control."""
    return CONTROL_BASELINE_SOURCE.format(control_key=control_key(leg))


# The recovery fixture by SOURCE reference (reader, path), never its content. phase27_relearn is
# not imported here (git_sha() at import); the fixture is never read or copied here.
RECOVERY_FIXTURE_SOURCE = (
    "phase27_relearn.disjointness_report",
    "results/phase16_recall_sample.json",
)

# =================================================================================================
# (9) THE ADMISSION CONTRACT (D-06, D-07, D-08, D-15 option 2) — frozen before any v5.0 number.
# =================================================================================================

EXPECTED_POINTS = len(ADVR_ARMS) * len(RATIO_GRID)
_TALLY_NAMES = (*V4_VERDICTS, REFUSED)
# D-15 option 2: cleared (a)(b)(c), second-seed replication not pre-registered. Never MOOT.
CANDIDATE_UNREPLICATED = "CANDIDATE-UNREPLICATED"
VERDICTS = ("ADMITTED", "MOOT", "INCONCLUSIVE", REFUSED, CANDIDATE_UNREPLICATED)

FRONTIER_SCHEMA = """The v5.0 frontier Phase 32 must emit (results/phase32_frontier.json), in the
v4.0 shape so point_verdict_string and cleared_abc apply unchanged:

  point_keys: list(POINT_KEYS()), in that order
  points[<key>].verdict.verdict: "PASS" | "FAIL" | "INCONCLUSIVE", or None with a non-empty
      points[<key>].verdict.early_return_reason (read as REFUSED)
  points[<key>].verdict.reasons: list of str, the route's reasons; the last one carries
      mitigation_gate.REPLICATION_PENDING_MARKER on a would-be PASS (GATE-08)
  points[<key>].verdict.<route kwargs>: the corrected_point_verdict inputs; on every measured
      (non-REFUSED) point control_taught_recall / control_heldout_recall are k/n of the leg's
      own advr control counts below, and the control point's point_*_recall are those counts
  verdicts.tallies: {PASS, FAIL, INCONCLUSIVE, REFUSED: count}, re-derived by admission()
  verdicts.tallies_by_leg[<leg>]: the same per leg, <leg> = <key>.rsplit("_", 1)[0]
  verdicts.control_readings[<leg>].recall_counts.{taught, heldout}: [k, n] int counts of the
      leg's own ratio-0 advr control

No promotion field is defined (D-15 option 2). admission() reads stored verdicts only; nothing
is decided after this record exists (D-06).
"""


def recall_threshold(frontier, leg, arm):
    """ADMIT-01 / D-06 / WR-05: ``(F_Y * k/n, k, n)`` from the arm's OWN ratio-0 control counts.

    Only ``arm == "advr"``: a DP reading never sources an adversarial threshold.
    """
    _prove(arm == "advr", f"arm {arm!r} refused: the threshold reads the advr control only")
    _prove(leg in LEGS, f"leg {leg!r} is not one of {LEGS}")
    k, n = frontier["verdicts"]["control_readings"][f"advr_{leg}"]["recall_counts"]["taught"]
    _prove_count("k", k)
    _prove_count("n", n)
    _prove(0 <= k <= n and n > 0, f"control taught recall {k}/{n} is not a count out of n > 0")
    return F_Y * (k / n), k, n


def _frontier_leg(key):
    return key.rsplit("_", 1)[0]


def _tally(strings):
    strings = list(strings)
    return {name: sum(1 for s in strings if s == name) for name in _TALLY_NAMES}


def _is_count_pair(pair):
    return (
        isinstance(pair, list)
        and len(pair) == len(("k", "n"))
        and all(isinstance(x, int) and not isinstance(x, bool) for x in pair)
        and 0 <= pair[0] <= pair[-1]
        and pair[-1] > 0
    )


def _control_readings(frontier):
    """``{leg: {"taught": [k, n], "heldout": [k, n]}}`` from the record, or None if malformed."""
    readings = frontier["verdicts"].get("control_readings")
    out = {}
    for leg in LEGS:
        entry = readings.get(f"advr_{leg}") if isinstance(readings, dict) else None
        counts = entry.get("recall_counts") if isinstance(entry, dict) else None
        if not isinstance(counts, dict):
            return None
        if not all(_is_count_pair(counts.get(side)) for side in ("taught", "heldout")):
            return None
        out[leg] = {side: list(counts[side]) for side in ("taught", "heldout")}
    return out


def _is_rate(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _own_control_mismatch(frontier, points, strings, readings):
    """(1d) The stored verdicts must re-derive from each leg's OWN advr ratio-0 control counts.

    D-11/D-12: a control outside (0,1] REFUSES its whole leg, so a measured (non-REFUSED) point
    beside it contradicts the record's own counts. D-06/WR-05: every measured point was graded
    against ``F_Y`` x that control, so its stored ``control_*_recall`` must be the counts' k/n,
    and the control point's own ``point_*_recall`` must be those counts — a point graded against
    any other reading (a ``dp_*`` one included) is indistinguishable from a forgery. A REFUSED
    point is checked on the fields it carries only (a D-12 short-circuit record was never routed).
    A learnable leg MAY carry REFUSED points: the route also refuses on its ceiling and retention
    floors, which D-11 does not own. Returns the first mismatch, or None.
    """
    for leg in LEGS:
        t, h = readings[leg]["taught"], readings[leg]["heldout"]
        _, k, n = recall_threshold(frontier, leg, "advr")
        expected = {"taught": k / n, "heldout": h[0] / h[1]}
        unlearnable = control_is_unlearnable(*t, *h)
        for key in leg_keys(leg):
            entry = points[key]["verdict"]
            measured = strings[key] != REFUSED
            if unlearnable and measured:
                return (
                    f"{key} reads {strings[key]} but advr_{leg}'s own control taught {t} / "
                    f"heldout {h} is unlearnable: D-11/D-12 REFUSE the whole leg"
                )
            fields = {f"control_{side}_recall": side for side in expected}
            if key == control_key(leg):
                fields |= {f"point_{side}_recall": side for side in expected}
            for field, side in fields.items():
                if field not in entry and not measured:
                    continue
                value = entry.get(field)
                if not (_is_rate(value) and math.isclose(value, expected[side], rel_tol=1e-12)):
                    return (
                        f"{key}.{field} {value!r} is not advr_{leg}'s own control reading "
                        f"{expected[side]!r} (WR-05)"
                    )
            carried = entry.get("control_recall_counts")
            if carried is not None and carried != readings[leg]:
                return f"{key}.control_recall_counts {carried!r} is not advr_{leg}'s own control"
    return None


def _result(verdict, reasons, admitted=(), readings=None):
    _prove(verdict in VERDICTS, f"admission verdict {verdict!r} outside {VERDICTS}")
    return {
        "verdict": verdict,
        "reasons": list(reasons),
        "admitted_point_keys": list(admitted),
        "control_readings": readings or {},
    }


def _inconclusive(reason):
    return _result("INCONCLUSIVE", [f"{reason} — could not tell, so not MOOT"])


def _leg_line(leg, readings):
    t, h = readings[leg]["taught"], readings[leg]["heldout"]
    return f"advr_{leg} control recall taught {t[0]}/{t[1]}, heldout {h[0]}/{h[1]}"


def admission(frontier):
    """THE ADMISSION CONTRACT (ADMIT-02). Returns ``{verdict, reasons, admitted_point_keys,
    control_readings}``, verdict in ``VERDICTS``. First hit returns, strictly in this order:

    (1a-1c) INCONCLUSIVE on an absent / mis-keyed / mis-shaped record, a verdict string outside
    PASS / FAIL / INCONCLUSIVE / REFUSED, non-list reasons, or tallies that do not re-derive —
    returned, never raised (T-29-14). (1d) INCONCLUSIVE when the stored verdicts do not re-derive
    from each leg's OWN advr control: a measured point beside an unlearnable control (D-11/D-12
    refuse the whole leg), or a point graded against any other reading (D-06/WR-05). An
    unlearnable or foreign control therefore never reaches ADMITTED, CANDIDATE or MOOT; admission
    reads stored verdicts and never re-labels them (D-06). (2) ADMITTED iff >= 1 stored PASS,
    naming every PASS key in POINT_KEYS() order (D-06). (3) CANDIDATE-UNREPLICATED (D-15 option
    2) iff some INCONCLUSIVE is the gate's replication-pending candidate. (4) REFUSED iff every
    point is REFUSED (D-07: the frontier could not be measured). (5) MOOT, naming every
    fully-REFUSED leg (D-08).
    """
    # (1a) shape
    if not isinstance(frontier, dict):
        return _inconclusive("frontier record absent")
    if not isinstance(frontier.get("verdicts"), dict):
        return _inconclusive("verdicts is absent or not a dict")
    keys = POINT_KEYS()
    points = frontier.get("points")
    if (
        frontier.get("point_keys") != list(keys)
        or not isinstance(points, dict)
        or set(points) != set(keys)
    ):
        return _inconclusive(
            f"point keys / entries do not equal the {EXPECTED_POINTS} pre-registered keys"
        )
    malformed = [
        k
        for k in keys
        if not (
            isinstance(points[k], dict)
            and isinstance(points[k].get("verdict"), dict)
            and "verdict" in points[k]["verdict"]
        )
    ]
    if malformed:
        return _inconclusive(f"point entries without a verdict dict: {malformed}")
    readings = _control_readings(frontier)
    if readings is None:
        return _inconclusive("control_readings lack advr [k, n] counts for every leg")
    # (1b) closed verdict domain + reasons type
    strings = {k: point_verdict_string(points[k]) for k in keys}
    outside = {k: s for k, s in strings.items() if s not in _TALLY_NAMES}
    if outside:
        return _inconclusive(f"verdict string(s) outside {_TALLY_NAMES}: {outside}")
    bad_reasons = [
        k
        for k in keys
        if strings[k] in V4_VERDICTS
        and not (
            isinstance(points[k]["verdict"].get("reasons"), list)
            and all(isinstance(r, str) for r in points[k]["verdict"]["reasons"])
        )
    ]
    if bad_reasons:
        return _inconclusive(f"verdict.reasons is not a list of str on {bad_reasons}")
    # (1c) tallies re-derive
    stored = frontier["verdicts"]
    tally = _tally(strings.values())
    by_leg = {}
    for k in keys:
        by_leg.setdefault(_frontier_leg(k), []).append(strings[k])
    tally_by_leg = {leg: _tally(values) for leg, values in by_leg.items()}
    if tally != stored.get("tallies") or tally_by_leg != stored.get("tallies_by_leg"):
        return _inconclusive("verdicts.tallies / tallies_by_leg do not re-derive from the entries")
    # (1d) the verdicts re-derive from each leg's OWN advr control (D-06, D-11, D-12, WR-05)
    mismatch = _own_control_mismatch(frontier, points, strings, readings)
    if mismatch:
        return _inconclusive(mismatch)

    # (2) ADMITTED
    passing = [k for k in keys if strings[k] == "PASS"]
    if passing:
        return _result(
            "ADMITTED",
            [f"{len(passing)} of {EXPECTED_POINTS} points PASS: {passing}; tallies {tally}"],
            passing,
            readings,
        )
    # (3) CANDIDATE-UNREPLICATED — only INCONCLUSIVE strings reach the frozen rule.
    candidates = [
        k
        for k in keys
        if strings[k] == "INCONCLUSIVE"
        and mitigation_gate.promote_to_full_fidelity(
            verdict=strings[k],
            reasons=points[k]["verdict"]["reasons"],
            curve_k=CURVE_K,
            full_k=FULL_K,
        )[0]
    ]
    if candidates:
        return _result(
            CANDIDATE_UNREPLICATED,
            [
                f"{len(candidates)} point(s) cleared (a)(b)(c) with replication pending: "
                f"{candidates}; tallies {tally}",
                "no promotion is pre-registered (D-15 option 2): a candidate, never MOOT",
            ],
            (),
            readings,
        )
    lines = [_leg_line(leg, readings) for leg in LEGS]
    # (4) REFUSED
    if tally[REFUSED] == EXPECTED_POINTS:
        return _result(
            REFUSED,
            [
                f"all {EXPECTED_POINTS} points REFUSED: the frontier could not be measured "
                "(not 'the mitigation held')",
                *lines,
            ],
            (),
            readings,
        )
    # (5) MOOT
    reasons = [f"0 of {EXPECTED_POINTS} points PASS; tallies {tally}"]
    for leg, line in zip(LEGS, lines):
        if tally_by_leg[f"advr_{leg}"][REFUSED] == len(leg_keys(leg)):
            reasons.append(
                f"advr_{leg} fully REFUSED ({line}); MOOT does not extend to that capacity"
            )
    reasons.append("MOOT: no measured point cleared the frontier — nothing to relearn")
    return _result("MOOT", reasons, (), readings)


# =================================================================================================
# (10) THE SCOPE RULE (D-10, PREREG-02).
# =================================================================================================

SCOPE_RULE = {
    "ADMITTED": "run RELRN-06..09 on each of admitted_point_keys",
    "MOOT": "RELRN-06..09 ship as a MOOT named limitation",
    REFUSED: "RELRN-06..09 ship as a named limitation: the frontier could not be measured",
    CANDIDATE_UNREPLICATED: (
        "RELRN-06..09 ship as a named limitation: candidate cleared (a)(b)(c), replication not "
        "pre-registered"
    ),
    "INCONCLUSIVE": "refuse to proceed: the frontier record is malformed",
}


def relearning_scope(admission_result):
    """D-10 scope for an ``admission()`` result; refuses (SystemExit) on INCONCLUSIVE."""
    verdict = admission_result["verdict"]
    _prove(verdict in VERDICTS, f"admission verdict {verdict!r} outside {VERDICTS}")
    _prove(verdict != "INCONCLUSIVE", SCOPE_RULE["INCONCLUSIVE"])
    return {
        "verdict": verdict,
        "rule": SCOPE_RULE[verdict],
        "relearn_point_keys": tuple(admission_result["admitted_point_keys"])
        if verdict == "ADMITTED"
        else (),
    }
