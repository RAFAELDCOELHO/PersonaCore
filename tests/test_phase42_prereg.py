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
import fnmatch
import hashlib
import inspect
import json
import math
import os
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

from test_phase29_prereg import _assert_frozen_before, _git, _planted  # noqa: E402
from test_phase35_prereg import (  # noqa: E402
    _docstring_nodes,
    _insert_at,
    _literal_failures,
    _slot_census_failures,
)
from test_phase36_prereg import (  # noqa: E402
    _entries_node,
    _entry_string_failures,
    _first_inner,
    _skip_failures,
    _untested_functions,
)

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
# Plan 42-06 removes each name once Rafael confirms or changes that default: all five confirmed
# at the 42-06 checkpoint (his rulings, 2026-10-14, quoted in 42-REVIEW.md Resolution).
_UNCONFIRMED = frozenset()
_CONFIRMED_LABEL = "confirmed by Rafael 2026-10-14"
_CONFIRMED = frozenset({"record_layout", "unit_order", "crash_rule", "rehearsal_shape", "d05_seam"})


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
    assert set(entries) == _DECISION_ENTRIES | _UNCONFIRMED | _CONFIRMED
    assert len(entries) == len(_DECISION_ENTRIES) + len(_UNCONFIRMED) + len(_CONFIRMED)
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
    assert phase42_prereg._DEFAULT == _DEFAULT_TEXT
    assert phase42_prereg._CONFIRMED == _CONFIRMED_LABEL
    for name, entry in phase42_prereg.ENTRIES.items():
        assert (_DEFAULT_TEXT in entry["derivation"]) == (name in _UNCONFIRMED), name
        assert (_CONFIRMED_LABEL in entry["derivation"]) == (name in _CONFIRMED), name
    assert len(_CONFIRMED) == 5 and not _UNCONFIRMED


# =================================================================================================
# (3) ANCESTRY (SC5, T-42-01): frozen before every results/phase42_* record. Honest at zero records
# and after them. Plan 42-09's threshold test imports _strictly_before and _first_add from here.
# =================================================================================================


def _strictly_before(x, y):
    run = subprocess.run(("git", "merge-base", "--is-ancestor", x, y), cwd=_ROOT, check=False)
    return x != y and run.returncode == 0


def _first_add(path):
    return _git("log", "--diff-filter=A", "--format=%H", "--", path).split()[-1]


def _phase42_records():
    return sorted(_git("ls-files", phase42_prereg.RECORD_GLOB).split())


def test_phase42_prereg_is_frozen_before_every_phase42_record():
    _assert_frozen_before(PREREG, _phase42_records())
    # NON-VACUITY (natural RED): the v6.0 pre-registration was added before this one existed.
    with pytest.raises(subprocess.CalledProcessError):
        _assert_frozen_before(PREREG, ["scripts/phase35_prereg.py"])


def test_this_test_file_is_first_added_before_every_phase42_record():
    # Only the FIRST add: a later fix to this file must not redden the guard forever.
    mine = _first_add("tests/test_phase42_prereg.py")
    for record in _phase42_records():
        assert _strictly_before(mine, _first_add(record)), record
    # NON-VACUITY: the same check against a file added long before this one is False.
    assert not _strictly_before(mine, _first_add("scripts/phase35_prereg.py"))


def test_records_at_commit_is_true_at_the_first_commit():
    first = _git("log", "--format=%H", "--", PREREG).split()[-1]
    at_first = _git("ls-tree", "-r", "--name-only", first, "--", "results/").split()
    assert at_first, "meta-guard: the first commit's results/ tree is empty, the check is vacuous"
    assert not [path for path in at_first if path.startswith("results/phase42_")]
    assert phase42_prereg.RECORDS_AT_COMMIT == 0


# =================================================================================================
# (4) NOTHING DERIVED IS TYPED (T-42-03): the 1e-3 node of LRS is the one exemption (D-02).
# =================================================================================================


def _lrs_node(tree):
    (node,) = [
        n
        for n in tree.body
        if isinstance(n, ast.Assign)
        and len(n.targets) == 1
        and isinstance(n.targets[0], ast.Name)
        and n.targets[0].id == "LRS"
    ]
    return node


def _without_lrs(source):
    """``source`` with the LRS assignment's value replaced by ``None`` (same line count)."""
    node = _lrs_node(ast.parse(source))
    lines = source.splitlines(keepends=True)
    blank = ["\n"] * (node.end_lineno - node.lineno)
    lines[node.lineno - 1 : node.end_lineno] = [" " * node.col_offset + "LRS = None\n", *blank]
    return "".join(lines)


def _chosen_lr_literals_outside_lrs(source):
    """Every float constant equal to the caller-chosen lr that lies outside the LRS node."""
    tree = ast.parse(source)
    inside = {id(n) for n in ast.walk(_lrs_node(tree))}
    return [
        n.lineno
        for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and type(n.value) is float and n.value == 1e-3
        if id(n) not in inside
    ]


def _census_sets():
    import mitigation_budget

    p = phase42_prereg
    budget = _record(p.BUDGET_RECORD)
    seeds = {
        phase35_prereg.E3_N,
        phase35_prereg.STEP_BUDGET,
        p.T_MAX,
        p.SEED,
        teach_persona.BATCH_SIZE,
        teach_persona.WARMUP_STEPS,
        p.T_MAX * teach_persona.WARMUP_STEPS // teach_persona.MAX_STEPS,
        *p.V4_CONTROL_COUNTS["taught"],
        *p.V4_CONTROL_COUNTS["heldout"],
        len(p.E3_GRID_SUBSET["cells"]),
    }
    floats = {
        teach_persona.LR,
        1e-3,
        phase35_prereg.F_Y,
        phase35_prereg.DELTA,
        mitigation_budget.CLIP_NORM,
        mitigation_budget.CONTROL_CLIP_NORM,
        *p.P22_ONSETS.values(),
        budget["front_hours"]["E3"],
        *(budget["unit_prices"][k] for k in budget["unit_prices"] if k.startswith("e3_")),
        *p.NOISED_SIGMAS,
    }
    assert len([k for k in budget["unit_prices"] if k.startswith("e3_")]) == 3, "meta-guard"
    assert all(type(f) is float for f in floats), "meta-guard: a census value is not a float"
    assert all(type(i) is int for i in seeds), "meta-guard: a census value is not an int"
    return seeds, floats


def test_no_derived_value_is_typed_in_the_prereg(tmp_path):
    seeds, floats = _census_sets()
    real = _ROOT / PREREG
    before = real.read_bytes()
    source = before.decode("utf-8")
    # The LRS literal holds 1e-3 by design (D-02); without it nothing derived is typed.
    assert _literal_failures(source, seeds, floats, set()), "meta-guard: LRS is not scanned"
    scanned = _without_lrs(source)
    assert scanned.count("\n") == source.count("\n")
    assert _literal_failures(scanned, seeds, floats, set()) == []
    assert _chosen_lr_literals_outside_lrs(source) == []
    plants = [
        ("seed.py", f"\nX = {phase42_prereg.SEED!r}\n"),
        ("onset.py", f"\nX = {phase42_prereg.P22_ONSETS[phase42_prereg.T_MAX]!r}\n"),
        ("hours.py", f"\nX = {phase42_prereg.ENTRIES['e3_hours']['value']['e3_line_hours']!r}\n"),
        ("lr.py", "\nX = 0.001\n"),
    ]
    for name, line in plants:
        planted = _planted(tmp_path, source, source + line, name)
        assert _literal_failures(_without_lrs(planted), seeds, floats, set()), name
    planted = _planted(tmp_path, source, source + plants[-1][1], "lr_outside.py")
    assert _chosen_lr_literals_outside_lrs(planted)
    assert real.read_bytes() == before


# =================================================================================================
# (5) ENTRIES: EXACTLY FOUR FIELDS, NO PROPOSER; THE PRIVATE HELPERS.
# =================================================================================================


def _good_entry():
    return {"value": 1, "derivation": "d", "kind": "derived", "source": "s"}


def test_entries_have_exactly_four_fields_and_no_proposer(tmp_path):
    assert phase42_prereg.ENTRY_FIELDS is phase35_prereg.ENTRY_FIELDS
    assert phase42_prereg.KINDS is phase35_prereg.KINDS
    assert phase42_prereg.FORBIDDEN_PHRASE is phase35_prereg.FORBIDDEN_PHRASE
    for name, entry in phase42_prereg.ENTRIES.items():
        assert set(entry) == {"value", "derivation", "kind", "source"}, name
    assert phase42_prereg._prove_entries() is None

    phase42_prereg._prove_entry("ok", _good_entry())
    refused = (
        {**_good_entry(), "proposer": "Rafael"},
        {**_good_entry(), "adopted_by": "Rafael"},
        {k: v for k, v in _good_entry().items() if k != "source"},
        {**_good_entry(), "kind": "guess"},
        {**_good_entry(), "derivation": ""},
        {**_good_entry(), "value": phase42_prereg.FORBIDDEN_PHRASE},
        [1],
    )
    for entry in refused:
        with pytest.raises(SystemExit, match=r"^\[phase42_prereg\]"):
            phase42_prereg._prove_entry("x", entry)

    real = _ROOT / PREREG
    before = real.read_bytes()
    source = before.decode("utf-8")
    entries = _entries_node(ast.parse(source))
    assert entries is not None, "meta-guard: _ENTRIES not found, the walk would be vacuous"
    assert _entry_string_failures(source) == []

    kind_key, _ = _first_inner(entries, "kind")
    planted_key = _insert_at(source, kind_key.lineno, kind_key.col_offset, '"proposer": "Rafael", ')
    ast.parse(planted_key)
    assert _entry_string_failures(_planted(tmp_path, source, planted_key, "key.py"))

    _, derivation = _first_inner(entries, "derivation")
    first = next(n for n in ast.walk(derivation) if isinstance(n, ast.Constant))
    planted_phrase = _insert_at(
        source, first.lineno, first.col_offset + 1, phase42_prereg.FORBIDDEN_PHRASE
    )
    ast.parse(planted_phrase)
    assert _entry_string_failures(_planted(tmp_path, source, planted_phrase, "phrase.py"))
    assert real.read_bytes() == before


def test_no_mutable_containers_in_entries():
    for name, entry in phase42_prereg.ENTRIES.items():
        assert isinstance(entry, types.MappingProxyType), name
        assert _no_mutable_containers(entry["value"]), name
    assert isinstance(phase42_prereg.ENTRIES, types.MappingProxyType)
    # NON-VACUITY: the predicate refuses a list, a dict and a set nested in a proxy.
    for bad in ([1], {"a": 1}, {1}):
        assert not _no_mutable_containers(types.MappingProxyType({"x": (bad,)}))


def test_prove_count_and_read_helpers():
    with pytest.raises(SystemExit, match=r"^\[phase42_prereg\] x$"):
        phase42_prereg._prove(False, "x")
    assert phase42_prereg._prove(True, "x") is None
    assert phase42_prereg._prove_count("n", 0) is None
    for bad in (True, -1, 1.5):
        with pytest.raises(SystemExit, match=r"^\[phase42_prereg\]"):
            phase42_prereg._prove_count("n", bad)
    read = phase42_prereg._read(phase42_prereg.BUDGET_RECORD)
    assert isinstance(read, dict) and "unit_caps" in read


# =================================================================================================
# (6) IMPORTING THE PREREG OPENS NO CHECKPOINT; THE SLOT CENSUS, ZERO SKIPS, EVERY FUNCTION CALLED.
# =================================================================================================


def _opens_a_checkpoint(path, repo):
    """True for a path under the repo's checkpoints/ or data/, or with a .pt / .safetensors
    suffix. Repo-relative, never a substring test: torch's own torch/utils/data is not data/."""
    if not isinstance(path, (str, os.PathLike)):
        return False
    resolved = pathlib.Path(path).resolve()
    return (
        resolved.is_relative_to(repo / "checkpoints")
        or resolved.is_relative_to(repo / "data")
        or resolved.suffix in (".pt", ".safetensors")
    )


_PROBE = """
import json, os, pathlib, sys

{predicate}

_REPO = pathlib.Path(sys.argv[1]).resolve()
_FLAGGED = []


def _hook(event, args):
    if event == "open" and args and _opens_a_checkpoint(args[0], _REPO):
        _FLAGGED.append(os.fspath(args[0]))


sys.addaudithook(_hook)
sys.path[:0] = [str(_REPO / "scripts"), str(_REPO / "src")]
import phase42_prereg

imported = list(_FLAGGED)
_FLAGGED.clear()
planted = [_REPO / "checkpoints" / "planted", _REPO / "data" / "planted", *sys.argv[2:]]
for path in planted:
    try:
        open(path, encoding="utf-8")
    except FileNotFoundError:
        pass
print(json.dumps({{
    "import_flagged": imported,
    "safetensors_loaded": "safetensors" in sys.modules,
    "cells": len(phase42_prereg.E3_GRID_SUBSET["cells"]),
    "planted": [os.fspath(p) for p in planted],
    "planted_flagged": list(_FLAGGED),
}}))
"""


def test_importing_the_prereg_opens_no_checkpoint(tmp_path):
    """This file loads torch through teach_persona and seed_list() by design; an "open" audit hook
    watches the import. Blind spot: safetensors opens files in Rust without a Python "open" audit
    event, so a safetensors read is invisible to the hook; the sys.modules leg covers it. The
    import runs git show (a subprocess), which is not an open of checkpoints/ or data/."""
    import torch.utils.data

    pt, st = tmp_path / "planted.pt", tmp_path / "planted.safetensors"
    script = _PROBE.format(predicate=inspect.getsource(_opens_a_checkpoint))
    out = subprocess.run(
        [sys.executable, "-c", script, str(_ROOT), str(pt), str(st)],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    result = json.loads(out.stdout.strip().splitlines()[-1])
    assert result["import_flagged"] == []
    assert result["safetensors_loaded"] is False
    assert result["cells"] == len(phase42_prereg.RECIPES) * len(phase35_prereg.E3_SIGMAS)
    # NON-VACUITY: one planted open per predicate branch, each flagged by the hook.
    assert len(result["planted"]) == 4
    assert result["planted_flagged"] == result["planted"]
    repo = _ROOT.resolve()
    assert _opens_a_checkpoint(repo / "checkpoints" / "planted", repo)
    assert _opens_a_checkpoint(repo / "data" / "planted", repo)
    assert _opens_a_checkpoint(pt, repo) and _opens_a_checkpoint(st, repo)
    assert not _opens_a_checkpoint(3, repo)
    # A site-packages torch/utils/data path is never flagged.
    assert not _opens_a_checkpoint(pathlib.Path(torch.utils.data.__file__), repo)


def _phase42_script_sources():
    paths = sorted(_SCRIPTS.glob("phase42_*.py"))
    sources = [(p.relative_to(_ROOT).as_posix(), p.read_text(encoding="utf-8")) for p in paths]
    assert PREREG in {rel for rel, _ in sources}, "meta-guard: the census would miss the prereg"
    return sources


def test_phase42_scripts_pass_the_slot_census():
    assert _slot_census_failures(_phase42_script_sources()) == []
    assert fnmatch.fnmatch(PREREG, phase35_prereg.owner_prereg_glob("e3_grid_subset"))


def test_no_skips_in_this_file(tmp_path):
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert _skip_failures(source) == []
    planted = source + '\n\ndef test_planted():\n    pytest.skip("x")\n'
    assert _skip_failures(_planted(tmp_path, source, planted, "skip.py"))


def test_census_every_phase42_prereg_function_has_a_cpu_test(tmp_path):
    real = _ROOT / PREREG
    before = real.read_bytes()
    source = before.decode("utf-8")
    test_source = pathlib.Path(__file__).read_text(encoding="utf-8")
    defs = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)]
    assert defs, "meta-guard: the prereg defines no function, the census would be vacuous"
    assert _untested_functions("phase42_prereg", source, test_source) == []

    planted = source + '\n\ndef planted_untested():\n    """Planted."""\n'
    copied = _planted(tmp_path, source, planted, "untested.py")
    assert _untested_functions("phase42_prereg", copied, test_source) == ["planted_untested"]
    assert real.read_bytes() == before


# =================================================================================================
# (7) FORBIDDEN TOKENS AND THE INTEGER-TEN WALL OVER EVERY PHASE 42 FILE. Plans 42-04 / 42-05 rely
# on this gate for the driver files. Tokens are built by concatenation so this file never holds
# one whole.
# =================================================================================================

_FORBIDDEN_TOKENS = (
    "train" + "_arm",
    "os" + "." + "replace",
    "inject" + "_lora",
    "mitigation" + "_point_verdict",
)


def _forbidden_token_failures(source, tokens):
    """Every Name / Attribute identifier and every non-docstring str constant containing one of
    ``tokens``; a dotted token ``mod.attr`` matches an Attribute ``attr`` on the Name ``mod``."""
    tree = ast.parse(source)
    docstrings = _docstring_nodes(tree)
    failures = []
    for node in ast.walk(tree):
        texts = []
        if isinstance(node, ast.Name):
            texts.append(node.id)
        elif isinstance(node, ast.Attribute):
            texts.append(node.attr)
            if isinstance(node.value, ast.Name):
                texts.append(f"{node.value.id}.{node.attr}")
        elif isinstance(node, ast.alias):  # import x / from m import x [as y]
            texts += [node.name, node.asname or ""]
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstrings
        ):
            texts.append(node.value)
        for token in tokens:
            if "." in token and not isinstance(node, (ast.Attribute, ast.Constant)):
                continue
            if any(token in text for text in texts):
                failures.append(f"{token} at line {node.lineno}")
    return failures


def _phase42_files():
    paths = sorted(_SCRIPTS.glob("phase42_*.py")) + sorted(
        (_ROOT / "tests").glob("test_phase42_*.py")
    )
    rels = {p.relative_to(_ROOT).as_posix() for p in paths}
    assert {PREREG, "tests/test_phase42_prereg.py"} <= rels, "meta-guard: a plan file is missed"
    return [(p.relative_to(_ROOT).as_posix(), p.read_text(encoding="utf-8")) for p in paths]


def test_no_forbidden_token_in_phase42_files():
    from test_phase21_sc5 import _PATTERNS

    for rel, source in _phase42_files():
        assert _forbidden_token_failures(source, _FORBIDDEN_TOKENS) == [], rel
        walled = [
            (rel, lineno)
            for lineno, line in enumerate(source.splitlines(), 1)
            if any(pattern.search(line) for pattern in _PATTERNS)
        ]
        assert walled == []
    # NON-VACUITY: a planted use of each token fails; the same token in a docstring passes.
    plants = (
        "x = " + "train" + "_arm" + "(1)\n",
        "import os\n" + "os" + "." + "replace('a', 'b')\n",
        "from personacore import " + "inject" + "_lora\n",
        "y = '" + "mitigation" + "_point_verdict" + "'\n",
    )
    for plant, token in zip(plants, _FORBIDDEN_TOKENS, strict=True):
        assert _forbidden_token_failures(plant, (token,)), token
        assert not _forbidden_token_failures(f'def f():\n    """{token}"""\n', (token,)), token
    wall_line = "assert x " + "==" + " 1" + "0"
    assert any(pattern.search(wall_line) for pattern in _PATTERNS)


# =================================================================================================
# (8) UNITS, RECORD PATHS, RUN IDS, TRAINING PREFIXES AND THE WARMUP RULE (plan 42-02 Task 1;
# D-05, D-19, D-20, D-22, record_layout, unit_order).
# =================================================================================================


def _is_grid_cell(recipe, sigma):
    return any(
        c["recipe"] == recipe and c["sigma"] == sigma
        for c in phase42_prereg.E3_GRID_SUBSET["cells"]
    )


def test_units_and_order():
    assert phase42_prereg.CONTROL_UNITS == (
        "control_lr3e-04_t800",
        "control_lr1e-03_t200",
        "control_lr1e-03_t800",
    )
    assert len(phase42_prereg.POINT_UNITS) == len(phase42_prereg.RECIPES) * len(
        phase42_prereg.NOISED_SIGMAS
    )
    assert phase42_prereg.POINT_UNITS[0] == "point_lr3e-04_t200_sigma0p500000"
    assert phase42_prereg.POINT_UNITS[-1] == "point_lr1e-03_t800_sigma1p000000"
    assert phase42_prereg.POINT_UNITS == tuple(
        f"point_{phase42_prereg.recipe_tag(r)}_{phase42_prereg.sigma_tag(s)}"
        for r in phase42_prereg.RECIPES
        for s in phase42_prereg.NOISED_SIGMAS
    )
    assert phase42_prereg.UNITS == phase42_prereg.CONTROL_UNITS + phase42_prereg.POINT_UNITS
    assert len(set(phase42_prereg.UNITS)) == len(phase42_prereg.UNITS)
    # The reused recipe is read from the grid's one reused cell, and has no control unit.
    assert phase42_prereg.REUSED_RECIPE == phase42_prereg.RECIPES[0]
    assert (
        f"control_{phase42_prereg.recipe_tag(phase42_prereg.REUSED_RECIPE)}"
        not in phase42_prereg.CONTROL_UNITS
    )
    for unit in phase42_prereg.UNITS:
        recipe, sigma = phase42_prereg.unit_cell(unit)
        assert _is_grid_cell(recipe, sigma), unit
        assert (sigma == phase42_prereg.CONTROL_SIGMA) == unit.startswith("control_"), unit
    assert phase42_prereg.unit_cell(phase42_prereg.POINT_UNITS[0]) == (
        phase42_prereg.RECIPES[0],
        phase42_prereg.NOISED_SIGMAS[0],
    )
    for bad in ("point_x", "control_lr3e-04_t200", None):
        with pytest.raises(SystemExit, match=r"^\[phase42_prereg\]"):
            phase42_prereg.unit_cell(bad)
    # The tag helpers refuse a recipe or sigma outside the grid.
    with pytest.raises(SystemExit, match=r"^\[phase42_prereg\]"):
        phase42_prereg.recipe_tag({"lr": 1e-2, "steps": phase35_prereg.STEP_BUDGET, "batch": 1})
    with pytest.raises(SystemExit, match=r"^\[phase42_prereg\]"):
        phase42_prereg.sigma_tag(0.25)
    assert phase42_prereg.sigma_tag(phase42_prereg.CONTROL_SIGMA) == "sigma0p000000"


def test_unit_records():
    assert (
        phase42_prereg.unit_record("control_lr1e-03_t200")
        == "results/phase42_control_lr1e-03_t200.json"
    )
    assert (
        phase42_prereg.unit_record("point_lr3e-04_t800_sigma1p000000")
        == "results/phase42_point_lr3e-04_t800_sigma1p000000.json"
    )
    for unit in phase42_prereg.CONTROL_UNITS:
        assert fnmatch.fnmatch(phase42_prereg.unit_record(unit), phase42_prereg.CONTROL_GLOB), unit
    for unit in phase42_prereg.POINT_UNITS:
        record = phase42_prereg.unit_record(unit)
        assert fnmatch.fnmatch(record, phase42_prereg.RECORD_GLOB), unit
        assert not fnmatch.fnmatch(record, phase42_prereg.CONTROL_GLOB), unit
    assert phase42_prereg.E3_RECORD == "results/phase42_recipes.json"
    assert phase42_prereg.REPORT_RECORD == "results/phase42_recipes_report.md"
    for record in (phase42_prereg.E3_RECORD, phase42_prereg.REPORT_RECORD):
        assert fnmatch.fnmatch(record, phase42_prereg.RECORD_GLOB)
        assert not fnmatch.fnmatch(record, phase42_prereg.CONTROL_GLOB)
    assert len({phase42_prereg.unit_record(u) for u in phase42_prereg.UNITS}) == len(
        phase42_prereg.UNITS
    )
    with pytest.raises(SystemExit, match=r"^\[phase42_prereg\]"):
        phase42_prereg.unit_record("point_x")


def _csv_rel(unit, rehearsal):
    csv = teach_persona.arm_outputs(
        f"dp_n{phase35_prereg.E3_N}",
        prefix=phase42_prereg.train_prefix(unit, rehearsal=rehearsal),
    )["csv"]
    return csv.relative_to(_ROOT).as_posix()


def test_run_ids_and_prefixes():
    assert phase42_prereg.run_id("control_lr1e-03_t200") == "v6/42/E3/control_lr1e-03_t200"
    with pytest.raises(SystemExit, match=r"^\[phase42_prereg\]"):
        phase42_prereg.run_id("point_x")
    for unit in phase42_prereg.UNITS:
        assert phase42_prereg.train_prefix(unit, rehearsal=False) == "phase42e3_" + unit
        assert phase42_prereg.train_prefix(unit, rehearsal=True) == "phase42rh_" + unit
        for rehearsal in (False, True):
            rel = _csv_rel(unit, rehearsal)
            assert not fnmatch.fnmatch(rel, phase42_prereg.RECORD_GLOB), rel
            assert not fnmatch.fnmatch(rel, phase42_prereg.CONTROL_GLOB), rel
        # Meta-guard: the record paths themselves do match.
        assert fnmatch.fnmatch(phase42_prereg.unit_record(unit), phase42_prereg.RECORD_GLOB), unit
    with pytest.raises(SystemExit, match=r"^\[phase42_prereg\]"):
        phase42_prereg.train_prefix("point_x", rehearsal=False)


def test_warmup_rule():
    before = (teach_persona.WARMUP_STEPS, teach_persona.LR, teach_persona.MAX_STEPS)
    assert phase42_prereg.warmup_for(phase35_prereg.STEP_BUDGET) == teach_persona.WARMUP_STEPS
    assert (
        phase42_prereg.warmup_for(phase42_prereg.T_MAX) == 80
    )  # D-05, the literal in the test only
    assert {t: phase42_prereg.warmup_for(t) for t in phase42_prereg.STEPS} == dict(
        phase42_prereg.WARMUPS
    )
    with pytest.raises(SystemExit, match=r"^\[phase42_prereg\]"):
        phase42_prereg.warmup_for(201)
    assert (teach_persona.WARMUP_STEPS, teach_persona.LR, teach_persona.MAX_STEPS) == before


# =================================================================================================
# (9) THE CLIP AND TRAIN_CONFIG RULES, AND THE THRESHOLD FILL'S KWARGS THROUGH THE REAL PHASE 35
# RULE ON PLANTED CONTROLS (plan 42-02 Task 2; D-06, D-07, D-12, D-19, RECIPE-03).
# =================================================================================================


def test_clip_rule():
    import mitigation_budget

    assert phase42_prereg.clip_norm_for(phase42_prereg.CONTROL_SIGMA) == (
        mitigation_budget.CONTROL_CLIP_NORM
    )
    for sigma in phase42_prereg.NOISED_SIGMAS:
        assert phase42_prereg.clip_norm_for(sigma) == mitigation_budget.CLIP_NORM
    assert mitigation_budget.CLIP_NORM == 1.3254119157791138  # D-06, the literal in the test only
    with pytest.raises(SystemExit, match=r"^\[phase42_prereg\]"):
        phase42_prereg.clip_norm_for(0.25)


def test_expected_train_config():
    v4 = _record(phase42_prereg.V4_CONTROL_RECORD)["training"]["train_config"]
    for recipe in phase42_prereg.RECIPES:
        expected = dict(
            v4,
            lr=recipe["lr"],
            max_steps=recipe["steps"],
            warmup_steps=phase42_prereg.warmup_for(recipe["steps"]),
        )
        got = phase42_prereg.expected_train_config(recipe)
        assert dict(got) == expected, dict(recipe)
        assert got["grad_clip"] == v4["grad_clip"] == 1.0
        with pytest.raises(TypeError):
            got["lr"] = 0.0
    assert dict(phase42_prereg.expected_train_config(phase42_prereg.REUSED_RECIPE)) == v4
    with pytest.raises(SystemExit, match=r"^\[phase42_prereg\]"):
        phase42_prereg.expected_train_config({"lr": 1e-2, "steps": 1, "batch": 1})


def test_threshold_fill_inputs_shape():
    p = phase42_prereg
    first, second = phase42_prereg.threshold_fill_inputs(), phase42_prereg.threshold_fill_inputs()
    assert first == second and first is not second
    assert first["derivation"] is not second["derivation"]
    assert first["grid"] is p.E3_GRID_SUBSET
    assert first["input_records"] == (
        p.V4_CONTROL_RECORD,
        *(phase42_prereg.unit_record(u) for u in p.CONTROL_UNITS),
    )
    derivation = first["derivation"]
    assert phase42_prereg._prove_entry("threshold_fill_inputs", derivation) is None
    keys = {
        (c["recipe"]["lr"], c["recipe"]["steps"], c["recipe"]["batch"], c["seed"])
        for c in p.E3_GRID_SUBSET["cells"]
    }
    assert isinstance(derivation["value"], tuple) and set(derivation["value"]) == keys
    assert len(derivation["value"]) == len(p.RECIPES)
    assert derivation["value"] == tuple(phase42_prereg.recipe_key(r) for r in p.RECIPES)
    for path in first["input_records"]:
        assert path in derivation["source"], path
    assert "4f45a91" in derivation["source"]
    assert phase42_prereg._RULING_CONTEXT.format("18") in derivation["source"]


def _plant_controls(root, counts):
    """The 3 new control records on ``root``, each with the contract fields the threshold rule
    reads; ``counts`` maps a unit to (taught k, held-out k)."""
    p = phase42_prereg
    taught_n = p.V4_CONTROL_COUNTS["taught"][1]
    heldout_n = p.V4_CONTROL_COUNTS["heldout"][1]
    for unit in p.CONTROL_UNITS:
        recipe, sigma = phase42_prereg.unit_cell(unit)
        tk, hk = counts[unit]
        path = root / phase42_prereg.unit_record(unit)
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "recipe": dict(recipe),
            "seed": p.SEED,
            "sigma": sigma,
            "taught_recall": {"numerator": tk, "denominator": taught_n},
            "heldout_recall": {"numerator": hk, "denominator": heldout_n},
        }
        path.write_text(json.dumps(record), encoding="utf-8")


def test_threshold_fill_runs_the_real_rule_on_planted_controls(tmp_path, monkeypatch):
    import phase29_prereg

    p = phase42_prereg
    v4_bytes = (_ROOT / p.V4_CONTROL_RECORD).read_bytes()
    v4_copy = tmp_path / p.V4_CONTROL_RECORD
    v4_copy.parent.mkdir(parents=True, exist_ok=True)
    v4_copy.write_bytes(v4_bytes)
    learnable = p.V4_CONTROL_COUNTS["taught"][0], p.V4_CONTROL_COUNTS["heldout"][0]
    unlearnable_unit = "control_lr1e-03_t800"
    counts = {u: (0, 0) if u == unlearnable_unit else learnable for u in p.CONTROL_UNITS}
    _plant_controls(tmp_path, counts)
    monkeypatch.setattr(phase35_prereg, "_REPO_ROOT", tmp_path)

    thresholds = phase35_prereg.fill(
        "e3_recall_threshold", **phase42_prereg.threshold_fill_inputs()
    )
    v4_key = (teach_persona.LR, phase35_prereg.STEP_BUDGET, teach_persona.BATCH_SIZE, p.SEED)
    assert set(thresholds) == set(phase42_prereg.recipe_key(r) for r in p.RECIPES)
    assert thresholds[v4_key]["control"] == p.V4_CONTROL_RECORD
    # The v4.0 key's thresholds; the literals in the test only.
    assert thresholds[v4_key]["taught"] == 0.5486111111111112
    assert thresholds[v4_key]["heldout"] == 0.3737654320987654
    refused_key = (1e-3, p.T_MAX, teach_persona.BATCH_SIZE, p.SEED)
    assert thresholds[refused_key] is phase29_prereg.REFUSED
    for unit in p.CONTROL_UNITS:
        key = phase42_prereg.recipe_key(phase42_prereg.unit_cell(unit)[0])
        if unit != unlearnable_unit:
            assert thresholds[key]["control"] == phase42_prereg.unit_record(unit), unit

    # Keyed by the record, never by position: a control whose recipe is another recipe's.
    swapped = tmp_path / phase42_prereg.unit_record("control_lr1e-03_t200")
    good = swapped.read_bytes()
    record = json.loads(good)
    record["recipe"] = dict(phase42_prereg.unit_cell("control_lr3e-04_t800")[0])
    swapped.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(SystemExit, match="D-17"):
        phase35_prereg.fill("e3_recall_threshold", **phase42_prereg.threshold_fill_inputs())
    swapped.write_bytes(good)

    # A tampered v4.0 copy: still valid JSON (meta-guard), refused by the SHA-256 check.
    assert v4_bytes.endswith(b"\n")
    tampered = v4_bytes[:-1] + b" "
    json.loads(tampered)
    v4_copy.write_bytes(tampered)
    with pytest.raises(SystemExit, match="byte-identical"):
        phase35_prereg.fill("e3_recall_threshold", **phase42_prereg.threshold_fill_inputs())
    # NON-VACUITY: restored, the same fill passes again.
    v4_copy.write_bytes(v4_bytes)
    assert phase35_prereg.fill("e3_recall_threshold", **phase42_prereg.threshold_fill_inputs())


# =================================================================================================
# (10) THE TRAINING CSV DIRECTORIES ARE GITIGNORED (plan 42-02 Task 3, T-42-09): a crashed run's
# results/phase42e3_* / phase42rh_* csv would red the clean-tree probes; no record is ignored.
# =================================================================================================


def _ignored(rel):
    run = subprocess.run(("git", "check-ignore", "-q", rel), cwd=_ROOT, check=False)
    assert run.returncode in (0, 1), run
    return run.returncode == 0


def test_training_csv_directories_are_gitignored():
    p = phase42_prereg
    for unit in p.UNITS:
        for rehearsal in (False, True):
            rel = _csv_rel(unit, rehearsal)
            assert rel.startswith("results/"), rel  # meta-guard: it lands under results/
            assert _ignored(rel), rel
            assert not fnmatch.fnmatch(rel, p.RECORD_GLOB), rel
    # NON-VACUITY: the records the ordering legs must see are not ignored.
    for unit in p.UNITS:
        assert not _ignored(phase42_prereg.unit_record(unit)), unit
    assert not _ignored(p.E3_RECORD)
    assert not _ignored(p.REPORT_RECORD)


# =================================================================================================
# (11) THE VERDICT, THE 4 x 2 TABLE WITH EACH RECIPE'S CONTROL RECALL, THE DESCRIPTIVE AND
# CONTROL-RETENTION READINGS, THE SUMMARY LINE AND THE NULL LEAD (plan 42-03 Task 1; RECIPE-03,
# D-12, D-13, D-14, D-15, D-18, D-23).
# =================================================================================================

# The v4.0 key's fill thresholds (test_threshold_fill_runs_the_real_rule_on_planted_controls); the
# literals in the test only.
_V4_THRESHOLD = {"taught": 0.5486111111111112, "heldout": 0.3737654320987654}
_HEDGES = ("ainda", "possivelmente")


def test_point_verdict_truth_table():
    import phase29_prereg

    p = phase42_prereg
    assert (p.PASSA, p.NAO_PASSA, p.REFUSED) == ("passa", "não passa", phase29_prereg.REFUSED)
    assert p.LABELS == (p.PASSA, p.NAO_PASSA, p.REFUSED)
    # Meta-guard: the tie is a real float tie.
    assert 553 / 1008 == _V4_THRESHOLD["taught"]
    cases = (
        ((553, 1008), (243, 648), _V4_THRESHOLD, "passa"),
        ((552, 1008), (648, 648), _V4_THRESHOLD, "não passa"),
        ((1008, 1008), (242, 648), _V4_THRESHOLD, "não passa"),
        ((0, 1008), (0, 648), _V4_THRESHOLD, "não passa"),
        ((1008, 1008), (648, 648), phase29_prereg.REFUSED, phase29_prereg.REFUSED),
        ((0, 1008), (0, 648), phase29_prereg.REFUSED, phase29_prereg.REFUSED),
    )
    for taught, heldout, threshold, expected in cases:
        assert phase42_prereg.point_verdict(taught, heldout, threshold) == expected
    for bad in ((1, 0), (True, 1008), (1009, 1008), (-1, 1008), (1.0, 1008)):
        with pytest.raises(SystemExit, match=r"^\[phase42_prereg\]"):
            phase42_prereg.point_verdict(bad, (0, 648), _V4_THRESHOLD)
        with pytest.raises(SystemExit, match=r"^\[phase42_prereg\]"):
            phase42_prereg.point_verdict((0, 1008), bad, phase29_prereg.REFUSED)
    assert phase42_prereg._rate((553, 1008)) == 553 / 1008


def _verdict_reads(source):
    """``point_verdict``'s argument names and every Name id, Attribute attr and str Constant in
    its body, its docstring excluded."""
    tree = ast.parse(source)
    (fn,) = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "point_verdict"]
    docstrings = _docstring_nodes(tree)
    read = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Name):
            read.add(node.id)
        elif isinstance(node, ast.Attribute):
            read.add(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if id(node) not in docstrings:
                read.add(node.value)
    return tuple(a.arg for a in fn.args.args + fn.args.kwonlyargs), read


def _descriptive_names(read):
    return sorted(
        name for name in read for word in ("retention", "dialogue", "gap", "clip") if word in name
    )


def test_point_verdict_reads_only_recall():
    args, read = _verdict_reads(_prereg_source())
    assert args == ("taught", "heldout", "threshold")
    assert read and "threshold" in read, "meta-guard: the walk collected nothing"
    assert _descriptive_names(read) == []
    # NON-VACUITY: a body reading retention fails; a docstring naming it passes.
    planted = (
        "def point_verdict(taught, heldout, threshold):\n"
        '    """x"""\n'
        '    return threshold, record["retention_ppl"]\n'
    )
    assert _descriptive_names(_verdict_reads(planted)[1]) == ["retention_ppl"]
    docstring_only = (
        "def point_verdict(taught, heldout, threshold):\n"
        '    """reads no retention, no dialogue gap, no clip"""\n'
        "    return threshold\n"
    )
    assert _descriptive_names(_verdict_reads(docstring_only)[1]) == []


def _control_recall(taught=(790, 1008), heldout=(346, 648)):
    return {
        phase42_prereg.recipe_tag(r): {"taught": taught, "heldout": heldout}
        for r in phase42_prereg.RECIPES
    }


def test_table_4x2_with_control_recall():
    p = phase42_prereg
    verdicts = {
        unit: p.LABELS[i % len(p.LABELS)] for i, unit in enumerate(phase42_prereg.POINT_UNITS)
    }
    rows = phase42_prereg.table(verdicts, _control_recall())
    assert len(rows) == len(p.RECIPES)
    for row, recipe in zip(rows, p.RECIPES, strict=True):
        assert isinstance(row, types.MappingProxyType)
        tag = phase42_prereg.recipe_tag(recipe)
        sigma_keys = [phase42_prereg.sigma_tag(s) for s in p.NOISED_SIGMAS]
        assert list(row) == ["recipe", *sigma_keys, "control_taught", "control_heldout"]
        assert row["recipe"] == tag
        for sigma, key in zip(p.NOISED_SIGMAS, sigma_keys, strict=True):
            assert row[key] == verdicts[f"point_{tag}_{key}"], (tag, sigma)
        assert row["control_taught"] == "790/1008"
        assert row["control_heldout"] == "346/648"
    # D-23: the control counts sit beside the label, never in it.
    other = phase42_prereg.table(verdicts, _control_recall((0, 1008), (0, 648)))
    for row, again in zip(rows, other, strict=True):
        assert row["control_taught"] != again["control_taught"]
        assert {k: v for k, v in row.items() if not k.startswith("control_")} == {
            k: v for k, v in again.items() if not k.startswith("control_")
        }
    refused = (
        ({u: v for u, v in verdicts.items() if u != p.POINT_UNITS[0]}, _control_recall()),
        ({**verdicts, "point_x": p.PASSA}, _control_recall()),
        ({**verdicts, p.POINT_UNITS[0]: "sim"}, _control_recall()),
        (verdicts, {k: v for k, v in list(_control_recall().items())[1:]}),
        (verdicts, {**_control_recall(), "lr1e-02_t200": {"taught": (0, 1), "heldout": (0, 1)}}),
        (verdicts, _control_recall(taught=(1009, 1008))),
        (verdicts, _control_recall(heldout=(0, 0))),
    )
    for bad_verdicts, bad_recall in refused:
        with pytest.raises(SystemExit, match=r"^\[phase42_prereg\]"):
            phase42_prereg.table(bad_verdicts, bad_recall)


def _fixture_record():
    return {
        "condition_c": {"retention_ppl": 4.25, "retention_total_tokens": 51234},
        "dialogue_gap": -0.5,
        "clip_bind_count": 3,
        "training": {"seconds": 812.5},
        "scoring_seconds": 1456.7,
    }


def test_descriptive_reading():
    reading = phase42_prereg.descriptive_reading(_fixture_record())
    assert isinstance(reading, types.MappingProxyType)
    assert dict(reading) == {
        "kind": "descriptive",
        "retention_ppl": 4.25,
        "retention_total_tokens": 51234,
        "dialogue_gap": -0.5,
        "clip_bind_count": 3,
        "train_seconds": 812.5,
        "scoring_seconds": 1456.7,
    }
    for path in (
        ("condition_c", "retention_ppl"),
        ("condition_c", "retention_total_tokens"),
        ("condition_c",),
        ("dialogue_gap",),
        ("clip_bind_count",),
        ("training", "seconds"),
        ("training",),
        ("scoring_seconds",),
    ):
        record = json.loads(json.dumps(_fixture_record()))
        parent = record
        for key in path[:-1]:
            parent = parent[key]
        del parent[path[-1]]
        with pytest.raises(SystemExit, match=r"^\[phase42_prereg\]"):
            phase42_prereg.descriptive_reading(record)
    assert phase42_prereg._field({"a": {"b": 1}}, "a", "b") == 1
    with pytest.raises(SystemExit, match=r"^\[phase42_prereg\] record has no a.c$"):
        phase42_prereg._field({"a": {"b": 1}}, "a", "c")


def test_control_retention_row():
    p = phase42_prereg
    v4 = _record(p.V4_CONTROL_RECORD)["condition_c"]["point_retention_ppl"]
    assert p.V4_CONTROL_RETENTION == v4
    recipe = p.RECIPES[-1]
    row = phase42_prereg.control_retention_row(recipe, 4.5)
    assert isinstance(row, types.MappingProxyType)
    assert row["recipe"] == phase42_prereg.recipe_tag(recipe)
    assert row["retention_ppl"] == 4.5
    assert row["v4_control_retention_ppl"] == v4
    assert row["difference"] == 4.5 - v4
    assert row["kind"] == "descriptive"
    assert "não muda rótulo" in row["text"]
    assert "verdict" not in row and "label" not in row
    assert not any(h in row["text"].lower() for h in _HEDGES)
    reused = phase42_prereg.control_retention_row(p.REUSED_RECIPE, p.V4_CONTROL_RETENTION)
    assert reused["difference"] == 0.0
    with pytest.raises(SystemExit, match=r"^\[phase42_prereg\]"):
        phase42_prereg.control_retention_row({"lr": 1e-2, "steps": 1, "batch": 1}, 4.5)


def test_summary_line():
    p = phase42_prereg
    assert len(p.POINT_UNITS) == 8  # D-14, the literal in the test only
    none = dict.fromkeys(p.POINT_UNITS, p.NAO_PASSA)
    assert phase42_prereg._prove_verdicts(none) is None
    assert phase42_prereg.summary_line(none) == "0 de 8 pontos passam; 0 REFUSED"
    mixed = dict(none)
    for unit in p.POINT_UNITS[:2]:
        mixed[unit] = p.PASSA
    for unit in p.POINT_UNITS[-2:]:
        mixed[unit] = p.REFUSED
    assert phase42_prereg.summary_line(mixed) == "2 de 8 pontos passam; 2 REFUSED"
    with pytest.raises(SystemExit, match=r"^\[phase42_prereg\]"):
        phase42_prereg.summary_line({**none, p.POINT_UNITS[0]: "sim"})
    with pytest.raises(SystemExit, match=r"^\[phase42_prereg\]"):
        phase42_prereg.summary_line(dict(list(none.items())[1:]))


def test_report_lead_null_case():
    p = phase42_prereg
    null = "nenhuma receita manteve o recall onde a garantia é vazia (0 de 8 pontos)"
    assert phase42_prereg.null_line() == null == p.ENTRIES["null_line"]["value"]
    combos = [dict.fromkeys(p.POINT_UNITS, label) for label in p.LABELS]
    one = dict.fromkeys(p.POINT_UNITS, p.NAO_PASSA)
    one[p.POINT_UNITS[3]] = p.PASSA
    refused_only = dict.fromkeys(p.POINT_UNITS, p.NAO_PASSA)
    refused_only[p.POINT_UNITS[0]] = p.REFUSED
    combos += [one, refused_only]
    for verdicts in combos:
        lead = phase42_prereg.report_lead(verdicts)
        assert "\n" not in lead
        if p.PASSA in verdicts.values():
            assert lead == phase42_prereg.summary_line(verdicts)
        else:
            assert lead == null
        for text in (lead, phase42_prereg.summary_line(verdicts)):
            assert not any(h in text.lower() for h in _HEDGES), text
    assert phase42_prereg.report_lead(one) == "1 de 8 pontos passam; 0 REFUSED"


# =================================================================================================
# (12) EVERY EPSILON READING, THE EXACT-RATIONAL ENUMERATION AND THE D-16 / D-17 READINGS (plan
# 42-03 Task 2; RECIPE-02, D-11, D-14, D-16, D-17, Pitfall 6). Epsilons are compared with
# math.isclose against records or a live recompute, never == a typed literal (T-42-12).
# =================================================================================================


def _grid_epsilons():
    return [
        phase42_prereg.point_epsilon(
            phase42_prereg.unit_cell(u)[1], phase42_prereg.unit_cell(u)[0]["steps"]
        )
        for u in phase42_prereg.POINT_UNITS
    ]


def _v4_point_record(sigma):
    import phase25_record

    key = phase25_record.point_key(f"dp_n{phase35_prereg.E3_N}", sigma)
    return json.loads(phase25_record.point_record_path(key).read_text(encoding="utf-8"))


def test_epsilon_per_point():
    import phase25_epsilon

    p = phase42_prereg
    for steps in p.STEPS:
        assert phase42_prereg.point_epsilon(p.CONTROL_SIGMA, steps) is None
    for sigma in p.NOISED_SIGMAS:
        record = _v4_point_record(sigma)
        assert record["selection_accounted"] is False
        assert math.isclose(
            phase42_prereg.point_epsilon(sigma, phase35_prereg.STEP_BUDGET),
            record["epsilon"],
            rel_tol=1e-12,
        )
        live = phase25_epsilon.point_epsilon_for_sigma(
            sigma, steps=p.T_MAX, delta=phase35_prereg.DELTA
        )
        assert math.isclose(phase42_prereg.point_epsilon(sigma, p.T_MAX), live, rel_tol=1e-12)
    epsilons = _grid_epsilons()
    assert len(epsilons) == len(p.POINT_UNITS)
    distinct = []
    for eps in epsilons:
        if not any(math.isclose(eps, d, rel_tol=1e-12) for d in distinct):
            distinct.append(eps)
    assert len(distinct) == 3


def test_composition():
    p = phase42_prereg
    epsilons = _grid_epsilons()
    total, delta_total = phase42_prereg.composition(epsilons)
    assert math.isclose(total, math.fsum(epsilons), rel_tol=1e-12)
    assert math.isclose(delta_total, len(p.POINT_UNITS) * phase35_prereg.DELTA, rel_tol=1e-12)
    with pytest.raises(ValueError, match="CONTROL_HAS_NO_EPSILON"):
        phase42_prereg.composition(
            [*epsilons, phase42_prereg.point_epsilon(p.CONTROL_SIGMA, p.T_MAX)]
        )
    assert p.SELECTION_ACCOUNTED is False
    assert p.SELECTION_ACCOUNTED is phase35_prereg.SELECTION_ACCOUNTED


def test_vacuous_bound():
    for eps in _grid_epsilons():
        assert phase42_prereg.vacuous_bound(eps) == 1.0
    assert phase42_prereg.vacuous_bound(0.0) == 0.5
    values = [phase42_prereg.vacuous_bound(e) for e in (0, 1, 2)]
    assert values == sorted(values) and len(set(values)) == 3
    assert math.isclose(phase42_prereg.vacuous_bound(1), math.e / (math.e + 1), rel_tol=1e-15)


def test_tpr_reading():
    p = phase42_prereg
    eps = phase42_prereg.point_epsilon(p.NOISED_SIGMAS[-1], phase35_prereg.STEP_BUDGET)
    assert math.isclose(eps, _v4_point_record(p.NOISED_SIGMAS[-1])["epsilon"], rel_tol=1e-12)
    reading = phase42_prereg.tpr_reading(eps)
    assert isinstance(reading, types.MappingProxyType)
    expected = math.log10(1 - phase35_prereg.DELTA) - eps / math.log(10)
    assert math.isclose(reading["log10_fpr_threshold"], expected, rel_tol=1e-12)
    assert reading["log10_fpr_threshold"] < -69  # 5.69e-70 at eps = 159.44
    for text in ("rearrangement", "Theorem 2.1", "FPR = 0", "TPR ≤ δ", "arXiv:1311.0776v4"):
        assert text in reading["sentence"], text
    assert f"10^{reading['log10_fpr_threshold']:.1f}" in reading["sentence"]
    # No overflow at the largest grid epsilon.
    assert math.isfinite(phase42_prereg.tpr_reading(max(_grid_epsilons()))["log10_fpr_threshold"])


def test_exact_disagreements():
    import fractions

    p = phase42_prereg
    assert fractions.Fraction(str(phase35_prereg.F_Y)) == fractions.Fraction(7, 10)
    taught, heldout = p.V4_CONTROL_COUNTS["taught"], p.V4_CONTROL_COUNTS["heldout"]
    assert phase42_prereg.exact_disagreements(_V4_THRESHOLD["taught"], taught, taught[1]) == []
    assert phase42_prereg.exact_disagreements(_V4_THRESHOLD["heldout"], heldout, heldout[1]) == []
    # NON-VACUITY: a threshold nudged one ulp up disagrees with the exact rule at the tie.
    nudged = math.nextafter(_V4_THRESHOLD["taught"], 1.0)
    found = phase42_prereg.exact_disagreements(nudged, taught, taught[1])
    assert found and 553 in found
    with pytest.raises(SystemExit, match=r"^\[phase42_prereg\]"):
        phase42_prereg.exact_disagreements(_V4_THRESHOLD["taught"], (1009, 1008), 1008)
    with pytest.raises(SystemExit, match=r"^\[phase42_prereg\]"):
        phase42_prereg.exact_disagreements(_V4_THRESHOLD["taught"], taught, 0)


def _reused_points(taught=(0, 1008), heldout=(0, 648)):
    p = phase42_prereg
    return {
        u: (taught, heldout)
        for u in p.POINT_UNITS
        if phase42_prereg.unit_cell(u)[0] == p.REUSED_RECIPE
    }


def test_d16_and_d17_readings():
    p = phase42_prereg
    points = _record("results/phase25_recall.json")["points"]
    assert set(p.V4_RECIPE_POINT_READINGS) == set(p.NOISED_SIGMAS)
    for sigma in p.NOISED_SIGMAS:
        point = points[f"dp_n{phase35_prereg.E3_N}_{phase42_prereg.sigma_tag(sigma)}"]
        assert dict(p.V4_RECIPE_POINT_READINGS[sigma]) == {
            "taught": (point["taught_recall"]["numerator"], point["taught_recall"]["denominator"]),
            "heldout": (
                point["heldout_recall"]["numerator"],
                point["heldout_recall"]["denominator"],
            ),
        }
    rows = phase42_prereg.d16_side_by_side(_reused_points())
    assert len(rows) == len(p.NOISED_SIGMAS)
    for row, sigma in zip(rows, p.NOISED_SIGMAS, strict=True):
        assert row["sigma"] == sigma
        assert row["e3"] == {"taught": (0, 1008), "heldout": (0, 648)}
        assert row["v4"] == p.V4_RECIPE_POINT_READINGS[sigma]
        assert (row["taught"], row["heldout"]) == ("repete", "repete")
        assert row["kind"] == "descriptive"
    moved = phase42_prereg.d16_side_by_side(_reused_points(taught=(5, 1008)))
    assert {(r["taught"], r["heldout"]) for r in moved} == {("não repete", "repete")}
    with pytest.raises(SystemExit, match=r"^\[phase42_prereg\]"):
        phase42_prereg.d16_side_by_side({**_reused_points(), p.POINT_UNITS[-1]: ((0, 1), (0, 1))})
    with pytest.raises(SystemExit, match=r"^\[phase42_prereg\]"):
        phase42_prereg.d16_side_by_side(dict(list(_reused_points().items())[1:]))

    held = phase42_prereg.d17_reading(dict.fromkeys(p.POINT_UNITS, p.NAO_PASSA))
    assert held["held"] is True and held["passing_cells"] == ()
    assert held["kind"] == "descriptive"
    assert "confirmada" in held["text"] and "não confirmada" not in held["text"]
    one = dict.fromkeys(p.POINT_UNITS, p.NAO_PASSA)
    one["point_lr1e-03_t200_sigma0p500000"] = p.PASSA
    missed = phase42_prereg.d17_reading(one)
    assert missed["held"] is False
    assert missed["passing_cells"] == (("lr1e-03_t200", "sigma0p500000"),)
    assert "não confirmada" in missed["text"]
    assert "lr1e-03_t200 sigma0p500000" in missed["text"]
    assert "um achado, não uma falha" in missed["text"]
    assert missed["kind"] == "descriptive"
    rendered = [
        held["text"],
        missed["text"],
        phase42_prereg.tpr_reading(max(_grid_epsilons()))["sentence"],
    ]
    for text in rendered:
        assert not any(h in text.lower() for h in _HEDGES), text
