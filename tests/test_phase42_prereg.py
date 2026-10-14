"""Plan 42-01: the Phase 42 pre-registration, fill file 1 (RECIPE-01 / RECIPE-04 fill; every
written decision D-01..D-23 as an entry), CPU-only.

What this file proves:
- the record globs and inputs are read from the Phase 35 registry; RECIPES is the 2x2 lr x T grid
  at batch teach_persona.BATCH_SIZE; one seed; the grid fill is the registry's object, reuses the
  v4.0 sigma = 0 control on exactly one cell and ran the P22 check for every T;
- the caps check runs at import for the grid's counts and for the sigma count.

It reads only tracked files and git history and writes nothing under results/.
"""

import ast
import collections.abc
import hashlib
import json
import math
import pathlib
import re
import subprocess
import sys
import types

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_TESTS = str(_ROOT / "tests")
if _TESTS not in sys.path:
    sys.path.insert(0, _TESTS)

import phase35_prereg  # noqa: E402  (scripts/ is not a package)
import phase36_caps  # noqa: E402  (same)
import phase36_prereg  # noqa: E402  (same)
import phase42_prereg  # noqa: E402  (same)
import teach_persona  # noqa: E402  (same; torch at import, as the prereg itself)

PREREG = "scripts/phase42_prereg.py"


def _prereg_source():
    return (_ROOT / PREREG).read_text(encoding="utf-8")


# =================================================================================================
# (1) RECORD GLOBS, RECIPES, SEED, THE GRID FILL AND THE CAPS (Task 1).
# =================================================================================================


def test_record_globs_from_the_registry():
    p = phase42_prereg
    assert p.RECORD_GLOB == "results/phase42_*"
    assert p.CONTROL_GLOB == "results/phase42_control_*.json"
    assert p.RECORD_GLOB in phase35_prereg.V6_RESULT_PATHS
    assert p.CONTROL_GLOB in phase35_prereg.V6_RESULT_PATHS
    grid_inputs = phase35_prereg.SLOTS["e3_grid_subset"]["input_records"]
    threshold_inputs = phase35_prereg.SLOTS["e3_recall_threshold"]["input_records"]
    assert p.BUDGET_RECORD == grid_inputs[0]
    assert p.V4_CONTROL_RECORD == grid_inputs[1] == threshold_inputs[1]


def test_grid_recipes_and_seed():
    p = phase42_prereg
    t_max = phase36_prereg.ENTRIES["e3_max_steps"]["value"]
    assert len(p.RECIPES) == 4
    assert len({tuple(sorted(r.items())) for r in p.RECIPES}) == len(p.RECIPES)
    for recipe in p.RECIPES:
        assert isinstance(recipe, types.MappingProxyType)
        assert set(recipe) == {"lr", "steps", "batch"}
        assert recipe["batch"] == teach_persona.BATCH_SIZE
    assert {r["lr"] for r in p.RECIPES} == {teach_persona.LR, 1e-3}
    assert {r["steps"] for r in p.RECIPES} == {phase35_prereg.STEP_BUDGET, t_max}
    assert p.T_MAX == t_max
    assert dict(p.RECIPES[0]) == {
        "lr": teach_persona.LR,
        "steps": phase35_prereg.STEP_BUDGET,
        "batch": teach_persona.BATCH_SIZE,
    }
    assert p.SEED == phase35_prereg.seed_list()[0]
    assert p.SEED == 1337  # D-03, the literal in the test only
    assert p.CONTROL_SIGMA == phase35_prereg.E3_SIGMAS[0]
    assert p.NOISED_SIGMAS == phase35_prereg.E3_SIGMAS[1:]


def test_grid_fill_cells():
    p = phase42_prereg
    grid = p.E3_GRID_SUBSET
    cells = grid["cells"]
    assert len(cells) == len(p.RECIPES) * len(phase35_prereg.E3_SIGMAS)
    for cell in cells:
        assert cell["seed"] == p.SEED
        assert cell["n"] == phase35_prereg.E3_N
    assert grid["n"] == phase35_prereg.E3_N
    assert grid["unit"] == phase35_prereg.E3_UNIT
    reused = [cell for cell in cells if cell["reuse"] is not None]
    assert len(reused) == 1
    (cell,) = reused
    assert cell["reuse"] == p.V4_CONTROL_RECORD
    assert dict(cell["recipe"]) == dict(p.RECIPES[0])
    assert cell["sigma"] == phase35_prereg.E3_SIGMAS[0]


def test_p22_onsets_are_checked(monkeypatch):
    p = phase42_prereg
    assert set(p.P22_ONSETS) == {phase35_prereg.STEP_BUDGET, p.T_MAX}
    assert p.P22_ONSETS is p.E3_GRID_SUBSET["p22_onset_sigma"]
    # Measured 2026-10-13 (42-RESEARCH Item 4); the literals live in this test only.
    assert math.isclose(p.P22_ONSETS[phase35_prereg.STEP_BUDGET], 0.07890181429684162, rel_tol=1e-9)
    assert math.isclose(p.P22_ONSETS[p.T_MAX], 0.15780356992036104, rel_tol=1e-9)
    assert all(s > onset for s in p.NOISED_SIGMAS for onset in p.P22_ONSETS.values())

    real = phase35_prereg.p22_onset_sigma

    def planted(steps):
        return max(p.NOISED_SIGMAS) if steps == p.T_MAX else real(steps)

    monkeypatch.setattr(phase35_prereg, "p22_onset_sigma", planted)
    with pytest.raises(SystemExit, match="P22"):
        phase35_prereg.fill(
            "e3_grid_subset",
            recipes=p.RECIPES,
            seed=p.SEED,
            input_records=(p.BUDGET_RECORD, p.V4_CONTROL_RECORD),
            derivation=p.ENTRIES["e3_grid_subset"],
        )


def test_v4_control_is_read_not_typed():
    p = phase42_prereg
    shown = subprocess.run(
        ["git", "show", f"v5.0:{p.V4_CONTROL_RECORD}"],
        cwd=_ROOT,
        capture_output=True,
        check=True,
    ).stdout
    assert p.V4_CONTROL_SHA256 == hashlib.sha256(shown).hexdigest()
    # D-03, the literals in the test only.
    assert p.V4_CONTROL_SHA256 == "0c23f6c11bb25aa53a4b01548c923668119d005bae5e0aa8d6e4e9f6bdcc76ed"
    assert dict(p.V4_CONTROL_COUNTS) == {"taught": (790, 1008), "heldout": (346, 648)}


def _caps_calls(source):
    return [
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "check_unit_caps"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "phase36_caps"
    ]


def test_caps_are_checked_at_import():
    calls = _caps_calls(_prereg_source())
    assert len(calls) == 2
    for call in calls:
        assert isinstance(call.args[0], ast.Constant) and call.args[0].value == "E3"
    expanded = [c for c in calls if len(c.keywords) == 1 and c.keywords[0].arg is None]
    assert len(expanded) == 1
    assert ast.unparse(expanded[0].keywords[0].value) == (
        "phase36_caps.counts_for('e3_grid_subset', E3_GRID_SUBSET)"
    )
    sigmas = [c for c in calls if [k.arg for k in c.keywords] == ["sigmas"]]
    assert len(sigmas) == 1
    assert ast.unparse(sigmas[0].keywords[0].value) == "len(phase35_prereg.E3_SIGMAS)"
    # The cap binds: one recipe more than the grid is refused.
    with pytest.raises(SystemExit, match="recipes"):
        phase36_caps.check_unit_caps("E3", recipes=len(phase42_prereg.RECIPES) + 1)


# =================================================================================================
# (2) THE ENTRIES: every decision D-01..D-23, the predictions and the planner defaults (Task 2).
# =================================================================================================

_CONTEXT_SHA = "dc578f9"
_CONTEXT_PATH = ".planning/phases/42-dp-sgd-recipe-search-at-large/42-CONTEXT.md"
_DEFAULT_TEXT = "default taken at plan time, not yet confirmed by Rafael"

_DECISION_ENTRIES = frozenset(
    {
        "e3_grid_subset",
        "batch_and_q",
        "v4_control_reuse",
        "one_seed",
        "warmup_rule",
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
    }
)
# Plan 42-06 replaces each with its confirmed form.
_UNCONFIRMED = frozenset(
    {"record_layout", "unit_order", "crash_rule", "rehearsal_shape", "d05_seam"}
)


def _record(rel):
    return json.loads((_ROOT / rel).read_text(encoding="utf-8"))


def _no_mutable_containers(value):
    if isinstance(value, (list, dict, set)):
        return False
    if isinstance(value, collections.abc.Mapping):
        return all(_no_mutable_containers(v) for v in value.values())
    if isinstance(value, tuple):
        return all(_no_mutable_containers(v) for v in value)
    return True


def test_entries_names_kinds_and_d_ids():
    entries = phase42_prereg.ENTRIES
    assert set(entries) == _DECISION_ENTRIES | _UNCONFIRMED
    assert len(entries) == len(_DECISION_ENTRIES) + len(_UNCONFIRMED)
    for name, entry in entries.items():
        assert re.search(r"\b(D-\d\d|RECIPE-\d\d)\b", entry["derivation"]), name
        assert _CONTEXT_SHA in entry["source"], name
        expected = "derived" if name in ("e3_hours", "v4_control_reuse") else "preference"
        assert entry["kind"] == expected, name
        assert _no_mutable_containers(entry["value"]), name
    reuse = entries["v4_control_reuse"]["value"]
    assert reuse["record"] == phase42_prereg.V4_CONTROL_RECORD
    assert reuse["sha256"] == phase42_prereg.V4_CONTROL_SHA256
    assert reuse["taught"] == phase42_prereg.V4_CONTROL_COUNTS["taught"]
    assert reuse["heldout"] == phase42_prereg.V4_CONTROL_COUNTS["heldout"]
    assert reuse["seed"] == _record(phase42_prereg.V4_CONTROL_RECORD)["seed"]


def test_every_decision_has_an_entry():
    derivations = [entry["derivation"] for entry in phase42_prereg.ENTRIES.values()]
    for n in range(1, 24):
        assert any(f"D-{n:02d}" in text for text in derivations), f"D-{n:02d}"


def test_e3_hours_is_computed_from_the_budget():
    p = phase42_prereg
    budget = _record(p.BUDGET_RECORD)
    prices = budget["unit_prices"]

    def price(steps):
        seconds = prices["e3_overhead_high"] + steps * prices["e3_per_step_high"]
        return (seconds + prices["e3_score_high"]) / 3600

    runs = [cell["recipe"]["steps"] for cell in p.E3_GRID_SUBSET["cells"] if cell["reuse"] is None]
    expected = sum(price(steps) for steps in runs)
    value = p.ENTRIES["e3_hours"]["value"]
    assert math.isclose(value["priced_hours"], expected, rel_tol=1e-12)
    assert math.isclose(value["priced_hours"], 5.370215732835186, rel_tol=1e-12)
    assert value["e3_line_hours"] == budget["front_hours"]["E3"]
    assert value["priced_hours"] < value["e3_line_hours"]
    derivation = p.ENTRIES["e3_hours"]["derivation"]
    for text in ("5.58", "6.23", "results/phase25_recall.json"):
        assert text in derivation, text


def test_predictions_are_recorded_before_any_run():
    import phase25_record

    value = phase42_prereg.ENTRIES["predictions"]["value"]
    assert set(value) == {"d16_v4_recipe_points", "d17_no_recipe_passes"}
    for text in value.values():
        assert "descriptive" in text
        assert "a mismatch is a finding, not a failure" in text
    d16 = value["d16_v4_recipe_points"]
    points = _record("results/phase25_recall.json")["points"]
    for sigma in phase42_prereg.NOISED_SIGMAS:
        point = points[phase25_record.point_key(f"dp_n{phase35_prereg.E3_N}", sigma)]
        for leg in ("taught_recall", "heldout_recall"):
            assert f"{point[leg]['numerator']}/{point[leg]['denominator']}" in d16, (sigma, leg)
    assert "0/1008" in d16 and "0/648" in d16
    d17 = value["d17_no_recipe_passes"]
    assert "T = 800" in d17 and "AdamW" in d17


def test_d18_d23_wording():
    d18 = phase42_prereg.ENTRIES["lr_control_outcome"]["derivation"]
    for text in (
        "phase29_prereg.control_is_unlearnable",
        "only",
        "changes no label",
        "same weight",
    ):
        assert text in d18, text
    assert "or degrade retention" not in d18
    d23 = phase42_prereg.ENTRIES["own_control_recall"]["derivation"]
    for text in ("D-23", "both legs", "D-12"):
        assert text in d23, text


def test_ruling_context_is_the_d18_d23_commit():
    (sha,) = re.findall(r"\(([0-9a-f]{7,40})\)", phase42_prereg._RULING_CONTEXT)
    ruled = subprocess.run(
        ["git", "show", f"{sha}:{_CONTEXT_PATH}"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "D-23: Each point publishes" in ruled
    assert "does NOT change any label" in ruled
    # NON-VACUITY (natural): the context as first written holds neither.
    first = subprocess.run(
        ["git", "show", f"{_CONTEXT_SHA}:{_CONTEXT_PATH}"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "D-23: Each point publishes" not in first
    assert "does NOT change any label" not in first
    for name in ("lr_control_outcome", "own_control_recall"):
        assert sha in phase42_prereg.ENTRIES[name]["source"], name


def test_d11_wording():
    d11 = phase42_prereg.ENTRIES["vacuous"]["derivation"]
    for text in (
        "e^ε/(e^ε+1)",
        "V6-PREREG-09.md:53",
        "rearrangement",
        "Theorem 2.1",
        "arXiv:1311.0776",
        "FPR = 0",
        "TPR ≤ δ",
    ):
        assert text in d11, text
    assert '"' + "TPR ≤ e^ε" not in d11


def test_defaults_are_labelled():
    for name, entry in phase42_prereg.ENTRIES.items():
        assert (_DEFAULT_TEXT in entry["derivation"]) == (name in _UNCONFIRMED), name
    assert phase42_prereg._DEFAULT == _DEFAULT_TEXT
