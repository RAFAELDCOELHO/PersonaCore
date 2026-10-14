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
