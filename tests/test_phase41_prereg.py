"""Plan 41-02: the Phase 41 pre-registration, fill file 1 (ERASE-04, ERASE-07 fills; ERASE-03, -05,
-06, -09, -10 written as entries), CPU-only.

What this file proves:
- the record paths are read from the Phase 35 registry, ORDERINGS is ("greedy", the filled
  alternative ordering), and the three fills that must precede every results/phase41_* record
  (e1_checkpoint_grid, e1_alternative_ordering, e1_condition_b_margin) are the registry's objects;
- the caps check runs at import with the grid's count only, never a K = 48 confirmation count.

It reads only tracked files and git history and writes nothing under results/.
"""

import ast
import fnmatch
import pathlib
import sys

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
import phase41_prereg  # noqa: E402  (same)

PREREG = "scripts/phase41_prereg.py"


def _prereg_source():
    return (_ROOT / PREREG).read_text(encoding="utf-8")


# =================================================================================================
# (1) RECORD PATHS, TARGETS, SEEDS AND THE THREE FILLS (Task 1).
# =================================================================================================


def test_record_paths_from_the_registry():
    v6 = phase35_prereg.V6_RESULT_PATHS
    slots = phase35_prereg.SLOTS
    p = phase41_prereg
    assert p.RECORD_GLOB == "results/phase41_*" and p.RECORD_GLOB in v6
    assert p.CALIBRATION_GLOB == "results/phase41_calibration_*.json" and p.CALIBRATION_GLOB in v6
    assert p.BAND_GLOB == "results/phase41_band_inputs_*.json" and p.BAND_GLOB in v6
    assert p.BUDGET_RECORD == slots["e1_checkpoint_grid"]["input_records"][0]
    assert p.CALIBRATION_CORPUS == slots["e1_condition_a_floors"]["input_records"][1]
    assert p.NOISE_FLOOR_RECORD == slots["e1_condition_c_band_inputs"]["input_records"][0]
    assert (
        p.calibration_record("greedy", 1337) == "results/phase41_calibration_greedy_seed1337.json"
    )
    assert p.band_record(2024, "gradient") == "results/phase41_band_inputs_gradient_seed2024.json"
    assert (
        p.cell_record("cat_name", "greedy", 1337)
        == "results/phase41_cell_cat_name_greedy_seed1337.json"
    )
    assert (
        p.k16_record("pet_name", "gradient", 2024, 48)
        == "results/phase41_k16_pet_name_gradient_seed2024_k048.json"
    )
    assert (
        p.k48_record("street", "greedy", 1337, 128)
        == "results/phase41_a2_street_greedy_seed1337_k128.json"
    )
    assert p.ERASURE_RECORD == "results/phase41_erasure.json"
    assert p.REPORT_RECORD == "results/phase41_erasure_report.md"

    unit_paths = []
    for target in p.TARGETS:
        for ordering in p.ORDERINGS:
            for seed in p.SEEDS:
                unit_paths.append(p.cell_record(target, ordering, seed))
                for checkpoint in p.GRID:
                    unit_paths.append(p.k16_record(target, ordering, seed, checkpoint))
                    unit_paths.append(p.k48_record(target, ordering, seed, checkpoint))
    expected = len(p.TARGETS) * len(p.ORDERINGS) * len(p.SEEDS) * (1 + 2 * len(p.GRID))
    assert len(unit_paths) == expected
    for path in unit_paths:
        assert fnmatch.fnmatch(path, p.RECORD_GLOB), path
        assert not fnmatch.fnmatch(path, p.CALIBRATION_GLOB), path
        assert not fnmatch.fnmatch(path, p.BAND_GLOB), path
    prep_paths = [
        f(*args)
        for ordering in p.ORDERINGS
        for seed in p.SEEDS
        for f, args in (
            (p.calibration_record, (ordering, seed)),
            (p.band_record, (seed, ordering)),
        )
    ]
    every = unit_paths + prep_paths + [p.ERASURE_RECORD, p.REPORT_RECORD]
    assert len(set(every)) == len(every)

    target, ordering, seed, checkpoint = p.TARGETS[0], p.ORDERINGS[0], p.SEEDS[0], p.GRID[0]
    bad_calls = (
        (p.calibration_record, ("random", seed)),
        (p.calibration_record, (ordering, seed + 1)),
        (p.band_record, (seed + 1, ordering)),
        (p.band_record, (seed, "random")),
        (p.cell_record, ("hometown", ordering, seed)),
        (p.cell_record, (target, "random", seed)),
        (p.cell_record, (target, ordering, seed + 1)),
        (p.k16_record, (target, ordering, seed, checkpoint + 1)),
        (p.k16_record, ("hometown", ordering, seed, checkpoint)),
        (p.k48_record, (target, ordering, seed, checkpoint + 1)),
        (p.k48_record, (target, "random", seed, checkpoint)),
    )
    for function, args in bad_calls:
        with pytest.raises(SystemExit, match=r"^\[phase41_prereg\]"):
            function(*args)


def test_grid_fill():
    grid = phase41_prereg.E1_CHECKPOINT_GRID
    assert grid["checkpoints"] == (16, 32, 48, 64, 128)
    assert grid["checkpoints"] == phase41_prereg.GRID
    assert grid["read_k"] == phase35_prereg.CURVE_K
    assert grid["confirm_k"] == phase35_prereg.FULL_FIDELITY_K
    assert grid["not_reached"] == phase35_prereg.NOT_REACHED
    first = grid["checkpoints"][0]
    reading = {first: {"curve_k_zero": True, "full_fidelity_k_zero": True}}
    stop = phase35_prereg.e1_stop(grid=grid, readings=reading)
    assert dict(stop) == {"stop": first, "judged": True}
    # NON-VACUITY: e1_stop accepts only the registered grid object, never an equal copy.
    with pytest.raises(SystemExit, match="fill"):
        phase35_prereg.e1_stop(grid=dict(grid), readings=reading)


def test_alternative_ordering_fill():
    filled = phase41_prereg.E1_ALTERNATIVE_ORDERING
    entry = phase41_prereg.ENTRIES["e1_alternative_ordering"]
    assert set(filled) == set(entry)
    for field in entry:
        assert filled[field] == entry[field], field
    assert filled["value"] == "gradient"
    assert phase41_prereg.ORDERINGS == ("greedy", "gradient")
    derivation = filled["derivation"]
    for phrase in (
        "-dNLL/ds_j",
        "largest",
        "never the absolute value",
        "value_span_nll_mean",
        "static",
        "Spearman",
        "re-ranked",
    ):
        assert phrase in derivation, phrase
    with pytest.raises(TypeError):
        filled["value"] = "greedy"


def test_margin_fill():
    margin = phase41_prereg.E1_CONDITION_B_MARGIN
    assert margin == phase35_prereg.e1_condition_b_margin()
    assert type(margin) is float


def test_targets_and_seeds_are_read():
    assert phase41_prereg.TARGETS == phase35_prereg.e1_targets()
    assert phase41_prereg.TARGETS == ("pet_name", "cat_name", "street", "sibling_name")
    assert phase41_prereg.SEEDS == phase35_prereg.e1_teaching_seeds()
    assert phase41_prereg.run_id("prep_greedy_seed1337") == "v6/41/E1/prep_greedy_seed1337"


def _caps_calls(source):
    return [
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "check_unit_caps"
    ]


def test_caps_are_checked_at_import():
    source = _prereg_source()
    calls = _caps_calls(source)
    assert len(calls) == 1
    (call,) = calls
    assert isinstance(call.func.value, ast.Name) and call.func.value.id == "phase36_caps"
    assert len(call.args) == 1 and isinstance(call.args[0], ast.Constant)
    assert call.args[0].value == "E1"
    assert len(call.keywords) == 1 and call.keywords[0].arg is None  # the ** expansion only
    counts = call.keywords[0].value
    assert isinstance(counts, ast.Call) and ast.unparse(counts.func) == "phase36_caps.counts_for"
    slot, grid = counts.args
    assert isinstance(slot, ast.Constant) and slot.value == "e1_checkpoint_grid"
    assert isinstance(grid, ast.Name) and grid.id == "E1_CHECKPOINT_GRID"
    assert not counts.keywords
    keywords = [
        k.arg for node in ast.walk(ast.parse(source)) for k in getattr(node, "keywords", ())
    ]
    assert "k48_confirms_per_cell" not in keywords
    # The import-time check is the grid's count, which the committed cap admits.
    counts = phase36_caps.counts_for("e1_checkpoint_grid", phase41_prereg.E1_CHECKPOINT_GRID)
    assert phase36_caps.check_unit_caps("E1", **counts) == counts
