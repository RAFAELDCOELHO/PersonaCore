"""Phase 29 PRE-REGISTRATION — the v5.0 adversarial-with-replay (``advr``) sweep's keys, result
paths, replay recipe, gate route and own-control refusal, committed before any v5.0 number exists.

WHAT THIS FREEZES. The 12 point keys (D-01) rendered by WRAPPING ``phase25_record.point_key``
(never editing it) under the ``advr`` arms; every v5.0 results path in ONE tuple,
``V5_RESULT_PATHS`` (D-02), with the ancestry pathspecs DERIVED from it (D-03); the replay recipe
as the DP arms' own expression, imported lazily (D-04); the gate route, ``F_Y`` and the ratio grid
BY REFERENCE (D-05); the unlearnable-own-control refusal predicate and the REFUSED record shape
(D-11..D-13); the complete key set with no retry/alternate surface (D-14); and the named
limitations (D-19 DEBT-04, D-17 TD-16-R1). NOT here, by CONTEXT D-15: the admission contract,
the verdict tuple, the scope rule, the D-09 relearning pins and any promotion path. Those are
D-15-dependent and are added after the developer's GATE-08 ruling (Plan 29-04).

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
}
