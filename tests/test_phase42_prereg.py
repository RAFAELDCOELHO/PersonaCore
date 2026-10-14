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
import hashlib
import math
import pathlib
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
