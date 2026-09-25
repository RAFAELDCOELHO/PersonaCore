"""Phase 30 v5.0 DRIVER — the ``advr`` sweep's schedule, per-point plan, recipe identity and its
OWN-CONTROL reader (ACTRL-01, ACTRL-02, and the refusal half of ARECIPE-02 / SC2).

THE ONLY CONTROL SOURCE IS ``phase29_prereg.control_key`` (D-14). Every recall floor, every
``control_gap`` dialogue pair and the relearning-Z baseline is read through ``own_control``, which
derives the control key from the pre-registration and nothing else. WR-05 — v4.0 read the
``adv_*`` arms' control off the DP ``sigma = 0`` record through ``phase25_points.control_key_for``,
``control_reading``, ``record_kwargs``, ``_adversarial_extras`` and
``phase25_promotion.control_readings`` — is closed here by never touching any of them: the AST
guard in ``tests/test_phase30_points.py`` reddens if a Phase 30..34 module does. A DP-sourced record
relabelled as the advr control is refused on its axis / q / clip_norm even when its recipe values
agree (D-15), and a control whose recipe differs from the point's at read time is refused (D-16).

``phase25_points`` IS IMPORTED, NEVER EDITED OR ASSIGNED INTO (D-13). ``point_plan`` below
re-implements the v4.0 plan with the SAME dict keys, so ``phase25_points.train_stage`` and
``measure_stage`` accept it unchanged in Phase 32; the v4.0 key parsers refuse every ``advr_*``
key, which is why they are not called.

SCHEDULE VS CANONICAL ORDER (D-17, D-18). ``phase29_prereg.POINT_KEYS()`` stays the canonical,
arm-major order. ``SWEEP_SCHEDULE()`` is the EXECUTION order, derived from it: the n8 control,
then the n64 control, then everything else. No key is typed here.

Trains nothing and writes nothing except, on request, write-once REFUSED records. Torch-free at
import: ``teach_persona`` is imported lazily inside the functions that need it.
"""

import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
_SRC = str(_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import mitigation_budget  # noqa: E402  (scripts/ is not a package)
import phase24_adversarial  # noqa: E402  (same)
import phase25_points  # noqa: E402  (same)
import phase29_prereg  # noqa: E402  (same)

SWEEP_SEED = phase25_points.SWEEP_SEED

# D-09: the pre-registered recipe fields plus the two Phase 30 adds, one identity per leg.
RECIPE_FIELDS = phase29_prereg._RECIPE_FIELDS | frozenset(
    ("min_refusal_scored_tokens", "replay_source")
)

# Resolved from the pre-registration's one path tuple, never retyped.
CALIBRATION_PATH = next(
    p for p in phase29_prereg.V5_RESULT_PATHS if p.startswith("results/phase30_")
)


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase30_points] {message}")


def leg_of(key):
    _prove(key in phase29_prereg.POINT_KEYS(), f"{key!r} is not one of the v5.0 point keys")
    return next(leg for leg in phase29_prereg.LEGS if key in phase29_prereg.leg_keys(leg))


def _arm_of_leg(leg):
    _prove(leg in phase29_prereg.LEGS, f"leg {leg!r} is not one of {phase29_prereg.LEGS}")
    arms = [arm for arm in phase29_prereg.ADVR_ARMS if arm == f"advr_{leg}"]
    _prove(len(arms) == 1, f"leg {leg!r} names no single advr arm in {phase29_prereg.ADVR_ARMS}")
    return arms[0]


def recipe_identity(leg):
    """The leg's recipe (D-09), every value imported; proves teach_persona agrees (D-10)."""
    import teach_persona as tp  # torch at import — lazy, so this module stays CPU-only

    n = len(tp.arm_spec(_arm_of_leg(leg))[0])
    _prove(n == int(leg.removeprefix("n")), f"arm_spec gives {n} facts for leg {leg!r}")
    _prove(
        tp.MAX_STEPS == mitigation_budget.STEP_BUDGET,
        f"teach_persona.MAX_STEPS {tp.MAX_STEPS} != mitigation_budget.STEP_BUDGET",
    )
    _prove(tp.SEED == SWEEP_SEED, f"teach_persona.SEED {tp.SEED} != the sweep seed {SWEEP_SEED}")
    recipe = {
        "n_facts": n,
        "replay_windows": phase29_prereg.replay_windows(n),
        "seed": SWEEP_SEED,
        "max_steps": mitigation_budget.STEP_BUDGET,
        "min_refusal_scored_tokens": phase24_adversarial.MIN_REFUSAL_SCORED_TOKENS,
        "replay_source": [
            pathlib.Path(getattr(tp, name.split(".", 1)[1])).relative_to(tp._REPO_ROOT).as_posix()
            for name in phase29_prereg.REPLAY_SOURCE
        ],
    }
    _prove(set(recipe) == RECIPE_FIELDS, f"recipe fields {sorted(recipe)} != RECIPE_FIELDS")
    return recipe


def prereg_recipe(recipe):
    """The ``phase29_prereg.refused_record`` shape: only the pre-registered fields."""
    return {field: recipe[field] for field in sorted(phase29_prereg._RECIPE_FIELDS)}


def _controls():
    return tuple(phase29_prereg.control_key(leg) for leg in phase29_prereg.LEGS)


def prove_controls_first(schedule):
    """D-17: an exact permutation of the keys, the n8 control then the n64 control first."""
    schedule = tuple(schedule)
    keys = phase29_prereg.POINT_KEYS()
    controls = _controls()
    _prove(
        len(schedule) == len(keys) and set(schedule) == set(keys),
        f"schedule of {len(schedule)} key(s) is not a permutation of the {len(keys)} v5.0 keys",
    )
    _prove(len(set(schedule)) == len(schedule), "schedule repeats a key")
    _prove(
        schedule[: len(controls)] == controls,
        f"schedule starts {schedule[: len(controls)]}, not the controls {controls}: a point "
        "would run before its leg's own control exists (ACTRL-02)",
    )
    return schedule


def SWEEP_SCHEDULE():
    """The execution order (D-18): derived from POINT_KEYS(), never typed. A function."""
    controls = _controls()
    return prove_controls_first(
        controls + tuple(k for k in phase29_prereg.POINT_KEYS() if k not in controls)
    )


def point_plan(key):
    """The v4.0 plan's dict keys for one advr point (D-13). Torch-free."""
    leg = leg_of(key)
    arm = _arm_of_leg(leg)
    members = [r for r in phase29_prereg.RATIO_GRID if phase29_prereg.point_key(arm, r) == key]
    _prove(len(members) == 1, f"{key!r} renders from {len(members)} grid member(s), not one")
    axis_value = members[0]
    prefix = "phase32_" + key[len(arm) + 1 :]
    _prove(
        not prefix.startswith(phase25_points.CALIBRATION_PREFIX_LITERAL),
        f"prefix {prefix!r} resolves under the calibration prefix",
    )
    control = phase29_prereg.control_key(leg)
    return {
        "point_key": key,
        "arm": arm,
        "axis": "ratio",
        "axis_value": axis_value,
        "is_dp": False,
        "is_control": key == control,
        "n_facts": int(leg.removeprefix("n")),
        "seed": SWEEP_SEED,
        "prefix": prefix,
        "dp_sigma": None,
        "dp_clip_norm": None,
        "adversarial_ratio": axis_value,
        # The adv twin's pin: its adversarial branch never parses a key.
        "pinned_mechanism": phase25_points.pinned_mechanism("adv_" + leg, axis_value),
        "point_epsilon": None,
        "accounting": None,
        "control_key": control,
    }
