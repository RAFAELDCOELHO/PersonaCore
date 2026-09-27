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

import json
import pathlib
import subprocess
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
import phase25_run  # noqa: E402  (same)
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
    # D-10 IN-04: the replay source is read from teach_persona, so every name must say so.
    for name in phase29_prereg.REPLAY_SOURCE:
        _prove(
            name.split(".", 1)[0] == "teach_persona",
            f"REPLAY_SOURCE entry {name!r} does not name teach_persona (IN-04)",
        )
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


# =================================================================================================
# THE OWN-CONTROL READER (D-14..D-16, WR-05) and the calibration-recipe refusal (SC2, D-09).
# =================================================================================================


def _diff(a, b):
    """Field names on which two recipe dicts differ (either side may be a non-dict)."""
    if not (isinstance(a, dict) and isinstance(b, dict)):
        return sorted(RECIPE_FIELDS)
    return sorted(f for f in set(a) | set(b) if a.get(f) != b.get(f))


def _tracked_json(rel, tracked, what):
    _prove(
        rel in set(tracked),
        f"{what} {rel} is not TRACKED (git ls-files). Only a committed record is read: one "
        "borrowed from the working tree could move after the fact",
    )
    # CR-01: the COMMITTED blob is what is read; a tracked file edited on disk is refused.
    shown = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=_ROOT, capture_output=True)
    _prove(shown.returncode == 0, f"{what} {rel} has no committed blob at HEAD")
    _prove(
        shown.stdout == (_ROOT / rel).read_bytes(),
        f"{what} {rel} differs from its committed blob: refusing a working-tree edit",
    )
    return json.loads(shown.stdout.decode("utf-8"))


def calibration_record(tracked):
    return _tracked_json(CALIBRATION_PATH, tracked, "the ARECIPE-02 calibration")


def require_calibrated_recipe(leg, recipe, tracked):
    """SC2's refusal half: ``recipe`` must equal the live identity AND the tracked calibration's."""
    _prove(
        isinstance(recipe, dict) and set(recipe) == RECIPE_FIELDS,
        f"recipe fields {_diff(recipe, dict.fromkeys(RECIPE_FIELDS))} are not RECIPE_FIELDS",
    )
    live = recipe_identity(leg)
    _prove(recipe == live, f"recipe differs from recipe_identity({leg!r}) on {_diff(recipe, live)}")
    calibrated = calibration_record(tracked)["recipe"][leg]
    _prove(
        recipe == calibrated,
        f"recipe differs from the calibration {CALIBRATION_PATH} for leg {leg!r} on "
        f"{_diff(recipe, calibrated)}: a point is never scored under an uncalibrated recipe",
    )
    return recipe


def own_control(key, tracked, *, point_recipe):
    """The leg's OWN advr ratio-0 control record — the ONLY floor / gap / baseline source."""
    leg = leg_of(key)
    ckey = phase29_prereg.control_key(leg)
    require_calibrated_recipe(leg, point_recipe, tracked)
    record = _tracked_json(
        phase29_prereg.point_record_path(ckey), tracked, "the own control record"
    )
    _prove(record.get("point_key") == ckey, f"control record names {record.get('point_key')!r}")
    _prove(
        record.get("arm") == _arm_of_leg(leg),
        f"control record arm {record.get('arm')!r} is not {_arm_of_leg(leg)!r}",
    )
    _prove(
        record.get("axis") == "ratio"
        and record.get("q") is None
        and record.get("clip_norm") is None,
        f"control record has axis {record.get('axis')!r}, q {record.get('q')!r}, clip_norm "
        f"{record.get('clip_norm')!r}: that is a DP sigma-axis record relabelled as the advr "
        "control (WR-05), refused whatever its recipe says",
    )
    _prove(
        record.get("recipe") == point_recipe,
        f"control recipe differs from the point's at read time on "
        f"{_diff(record.get('recipe'), point_recipe)} (D-16)",
    )
    # WR-04: the declared recipe is not enough; what the control TRAINED with must agree too.
    config = (record.get("training") or {}).get("train_config") or {}
    trained = {
        "seed": (record.get("seed"), config.get("seed")),
        "max_steps": (config.get("max_steps"), record.get("composed_steps")),
    }
    off = sorted(f for f, got in trained.items() if any(v != point_recipe[f] for v in got))
    _prove(
        not off,
        f"control record trained with {trained}, not the point's recipe on {off} (D-16, WR-04): "
        "its declared recipe is not what it ran",
    )
    # D-19, WR-04: the control must also have drawn its recipe's replay on every step.
    per_step = (record.get("replay") or {}).get("per_step")
    _prove(
        per_step == [point_recipe["replay_windows"]] * point_recipe["max_steps"],
        "control record's declared replay recipe is not what its training drew, counted per step "
        f"through on_draw (D-07) (D-19, WR-04): replay per_step {per_step!r} != "
        f"[{point_recipe['replay_windows']}] * {point_recipe['max_steps']}",
    )
    return record


def control_floors(key, tracked, *, point_recipe):
    """``((taught_k, taught_n), (heldout_k, heldout_n))`` from the own control."""
    record = own_control(key, tracked, point_recipe=point_recipe)
    t, h = record["taught_recall"], record["heldout_recall"]
    return (t["numerator"], t["denominator"]), (h["numerator"], h["denominator"])


def control_dialogue_pair(key, tracked, *, point_recipe):
    """``control_gap``'s (adapter_on, adapter_off) pair, own-sourced."""
    cc = own_control(key, tracked, point_recipe=point_recipe)["condition_c"]
    return {"adapter_on": cc["point_dialogue_ppl_on"], "adapter_off": cc["point_dialogue_ppl_off"]}


def control_baseline(key, tracked, *, point_recipe):
    """The relearning-Z baseline: the own control's adapter digest and its source reference."""
    record = own_control(key, tracked, point_recipe=point_recipe)
    return {
        "source": phase29_prereg.control_baseline_source(leg_of(key)),
        "adapter_sha256": record["adapter_sha256"],
    }


def next_action(key, tracked):
    """D-19: what to do for ``key`` now. Trains nothing and writes nothing."""
    _prove(key in SWEEP_SCHEDULE(), f"{key!r} is not on the v5.0 schedule")
    leg = leg_of(key)
    ckey = phase29_prereg.control_key(leg)
    recipe = recipe_identity(leg)
    if key == ckey:
        # D-11/SC2: no control trains before the tracked ARECIPE-02 calibration exists and matches.
        require_calibrated_recipe(leg, recipe, tracked)
        return {"action": "train", "plan": point_plan(key)}
    (tk, tn), (hk, hn) = control_floors(key, tracked, point_recipe=recipe)
    if phase29_prereg.control_is_unlearnable(tk, tn, hk, hn):
        return {
            "action": "refuse",
            "records": {
                k: phase29_prereg.refused_record(
                    k, taught=(tk, tn), heldout=(hk, hn), recipe=prereg_recipe(recipe)
                )
                for k in phase29_prereg.leg_keys(leg)
                if k != ckey
            },
        }
    return {"action": "train", "plan": point_plan(key)}


def write_refused_records(records):
    """Write-once, resumable (WR-05): the WHOLE leg's non-control keys, every blob serialised
    before any write, and a target that already exists is accepted only if byte-identical to the
    blob it would receive. A write killed part-way is completed by the retry. Returns the paths
    written by this call."""
    legs = {leg_of(key) for key in records}
    _prove(len(legs) == 1, f"records span legs {sorted(legs)}, not one")
    (leg,) = legs
    expected = set(phase29_prereg.leg_keys(leg)) - {phase29_prereg.control_key(leg)}
    _prove(set(records) == expected, f"records {sorted(records)} are not leg {leg}'s non-controls")
    # atomic_write_json's own serialisation, so an existing file compares byte for byte.
    payloads = {key: json.dumps(records[key], sort_keys=True) for key in records}
    outs = {key: _ROOT / phase29_prereg.point_record_path(key) for key in records}
    existing = [key for key in records if outs[key].exists()]
    differ = sorted(
        str(outs[k]) for k in existing if outs[k].read_text(encoding="utf-8") != payloads[k]
    )
    _prove(not differ, f"REFUSING to overwrite existing record(s) {differ}")
    return [
        phase25_run.atomic_write_json(outs[key], records[key])
        for key in records
        if key not in existing
    ]
