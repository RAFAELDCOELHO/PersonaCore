"""Plan 42-09: the e3_recall_threshold fill (RECIPE-03; 42-CONTEXT D-12, D-18, D-19), CPU-only.

What this file proves:
- scripts/phase42_threshold_prereg.py fills every grid recipe's threshold as F_Y x ITS OWN sigma = 0
  control's recall on each leg, read from the committed control records (the v4.0 recipe's from
  the reused v4.0 record), REFUSED exactly when phase29_prereg.control_is_unlearnable holds;
  nothing typed;
- every consumed path is named in its derivation's source and tracked;
- the file imports only pathlib, sys, phase35_prereg and phase42_prereg, and importing it opens no
  checkpoint or data/ file;
- it is committed after every declared input and before every later results/phase42_* record
  (Phase 35 legs (a)/(b));
- Pitfall 6: every k where the fill's float comparison and the exact rational disagree is
  enumerated per recipe and leg, and equals the list shown to Rafael at 42-09 Task 1.

It reads only tracked files and git history and writes nothing under results/.
"""

import ast
import fnmatch
import inspect
import json
import pathlib
import subprocess
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

import phase29_prereg  # noqa: E402  (scripts/ is not a package)
import phase35_prereg  # noqa: E402  (same)
import phase42_prereg  # noqa: E402  (same)

from test_phase29_prereg import _assert_frozen_before, _git, _planted  # noqa: E402
from test_phase35_prereg import _slot_census_failures  # noqa: E402
from test_phase36_prereg import _skip_failures  # noqa: E402
from test_phase42_prereg import (  # noqa: E402
    _first_add,
    _opens_a_checkpoint,
    _phase42_records,
    _strictly_before,
)

THRESHOLD = "scripts/phase42_threshold_prereg.py"
THIS = "tests/test_phase42_threshold_prereg.py"
SLOT = "e3_recall_threshold"
LEGS = ("taught", "heldout")

# Pitfall 6 / plan-phase ruling 5: phase42_prereg.exact_disagreements per recipe tag and leg, as
# printed and shown to Rafael at 42-09 Task 1 (every list empty on both legs of all four recipes).
_DECLARED_DISAGREEMENTS = {
    "lr3e-04_t200": {"taught": [], "heldout": []},
    "lr3e-04_t800": {"taught": [], "heldout": []},
    "lr1e-03_t200": {"taught": [], "heldout": []},
    "lr1e-03_t800": {"taught": [], "heldout": []},
}


@pytest.fixture(scope="module")
def threshold():
    import phase42_threshold_prereg

    return phase42_threshold_prereg


def _read(rel):
    return json.loads((_ROOT / rel).read_text(encoding="utf-8"))


def _tracked(rel):
    return _git("ls-files", "--", rel) == rel


def _control_path(recipe):
    """The control record of one grid recipe: the reused v4.0 record, or its own control unit's."""
    if recipe == phase42_prereg.REUSED_RECIPE:
        return phase42_prereg.V4_CONTROL_RECORD
    (unit,) = [u for u in phase42_prereg.CONTROL_UNITS if phase42_prereg.unit_cell(u)[0] == recipe]
    return phase42_prereg.unit_record(unit)


def _control_counts(recipe):
    """``{leg: (k, n)}`` of one recipe's control, read here from the committed record (the reused
    v4.0 key from V4_CONTROL_COUNTS)."""
    if recipe == phase42_prereg.REUSED_RECIPE:
        return dict(phase42_prereg.V4_CONTROL_COUNTS)
    record = _read(_control_path(recipe))
    return {
        leg: (record[f"{leg}_recall"]["numerator"], record[f"{leg}_recall"]["denominator"])
        for leg in LEGS
    }


# =================================================================================================
# (1) THE VALUES ARE THE COMMITTED RECORDS' (RECIPE-03, D-12, D-18, D-19).
# =================================================================================================


def test_thresholds_are_computed_from_the_committed_records(threshold):
    fill = threshold.E3_RECALL_THRESHOLD
    recipes = phase42_prereg.RECIPES
    assert set(fill) == {phase42_prereg.recipe_key(r) for r in recipes}
    for recipe in recipes:
        value = fill[phase42_prereg.recipe_key(recipe)]
        path = _control_path(recipe)
        assert _tracked(path), path
        counts = _control_counts(recipe)
        (tk, tn), (hk, hn) = counts["taught"], counts["heldout"]
        if phase29_prereg.control_is_unlearnable(tk, tn, hk, hn):
            assert value == phase29_prereg.REFUSED, recipe
            continue
        # Recomputed ONLY to compare with the fill's value.
        assert dict(value) == {
            "control": path,
            "taught": phase35_prereg.F_Y * tk / tn,
            "heldout": phase35_prereg.F_Y * hk / hn,
        }, recipe


def test_every_consumed_path_is_in_its_derivation_source():
    inputs = phase42_prereg.threshold_fill_inputs()
    expected = (phase42_prereg.V4_CONTROL_RECORD,) + tuple(
        phase42_prereg.unit_record(u) for u in phase42_prereg.CONTROL_UNITS
    )
    assert tuple(inputs["input_records"]) == expected
    for path in inputs["input_records"]:
        assert path in inputs["derivation"]["source"], path
        assert _tracked(path), path


# =================================================================================================
# (2) IMPORTS ONLY, OPENS NO CHECKPOINT.
# =================================================================================================


def _own_imports(source):
    """Every module name the source imports, anywhere in it."""
    names = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            names.add(node.module)
    return names


def test_the_threshold_file_imports_only_pathlib_sys_and_the_two_preregs(tmp_path):
    source = (_ROOT / THRESHOLD).read_text(encoding="utf-8")
    allowed = {"pathlib", "sys", "phase35_prereg", "phase42_prereg"}
    assert _own_imports(source) == allowed
    planted = _planted(tmp_path, source, source + "\nimport phase29_prereg\n", "imports.py")
    assert _own_imports(planted) - allowed == {"phase29_prereg"}


_PROBE = """
import importlib.util, json, os, pathlib, sys

{predicate}

_REPO = pathlib.Path(sys.argv[1]).resolve()
_FLAGGED = []


def _hook(event, args):
    if event == "open" and args and _opens_a_checkpoint(args[0], _REPO):
        _FLAGGED.append(os.fspath(args[0]))


sys.addaudithook(_hook)
spec = importlib.util.spec_from_file_location("phase42_threshold_prereg", _REPO / sys.argv[2])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

imported = list(_FLAGGED)
_FLAGGED.clear()
planted = [_REPO / "checkpoints" / "planted", _REPO / "data" / "planted", *sys.argv[3:]]
for path in planted:
    try:
        open(path, encoding="utf-8")
    except FileNotFoundError:
        pass
print(json.dumps({{
    "import_flagged": imported,
    "safetensors_loaded": "safetensors" in sys.modules,
    "keys": len(module.E3_RECALL_THRESHOLD),
    "planted": [os.fspath(p) for p in planted],
    "planted_flagged": list(_FLAGGED),
}}))
"""


def test_importing_the_threshold_file_opens_no_checkpoint(tmp_path):
    # A fresh process with no scripts/ on sys.path loads the file by path: its own sys.path
    # inserts must reach both preregs, and the open audit hook sees no checkpoints/ or data/ path.
    pt, st = tmp_path / "planted.pt", tmp_path / "planted.safetensors"
    script = _PROBE.format(predicate=inspect.getsource(_opens_a_checkpoint))
    out = subprocess.run(
        [sys.executable, "-c", script, str(_ROOT), THRESHOLD, str(pt), str(st)],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    result = json.loads(out.stdout.strip().splitlines()[-1])
    assert result["import_flagged"] == []
    assert result["safetensors_loaded"] is False
    assert result["keys"] == len(phase42_prereg.RECIPES)
    # NON-VACUITY: one planted open per predicate branch, each flagged by the same hook.
    assert len(result["planted"]) == 4
    assert result["planted_flagged"] == result["planted"]


# =================================================================================================
# (3) ORDERING (Phase 35 legs (a)/(b)): after every declared input, before every later
# results/phase42_* record. Honest at zero later records and after them.
# =================================================================================================


def _first_commit(path):
    return _git("log", "--format=%H", "--", path).split()[-1]


def _declared_inputs():
    return sorted(phase42_prereg.threshold_fill_inputs()["input_records"])


def _later_records():
    return [p for p in _phase42_records() if not fnmatch.fnmatch(p, phase42_prereg.CONTROL_GLOB)]


def _first_control():
    return phase42_prereg.unit_record(phase42_prereg.CONTROL_UNITS[0])


def test_every_declared_input_precedes_the_threshold_file():
    first = _first_commit(THRESHOLD)
    inputs = _declared_inputs()
    assert len(inputs) == len(phase42_prereg.CONTROL_UNITS) + 1
    # The same set Phase 35 leg (b) reads: the tracked files matching the slot's input patterns.
    leg_b = {
        path
        for pattern in phase35_prereg.SLOTS[SLOT]["input_records"]
        for path in _git("ls-files", pattern).split()
    }
    assert leg_b == set(inputs)
    for path in inputs:
        assert _strictly_before(_first_add(path), first), path
    # NON-VACUITY (natural RED): the reverse relation is False for every input.
    assert not any(_strictly_before(first, _first_add(path)) for path in inputs)


def test_threshold_file_is_frozen_before_every_later_phase42_record():
    controls = [p for p in _phase42_records() if fnmatch.fnmatch(p, phase42_prereg.CONTROL_GLOB)]
    assert controls == sorted(phase42_prereg.unit_record(u) for u in phase42_prereg.CONTROL_UNITS)
    _assert_frozen_before(THRESHOLD, _later_records())
    # NON-VACUITY (natural RED): the threshold file was committed after the control records.
    with pytest.raises(subprocess.CalledProcessError):
        _assert_frozen_before(THRESHOLD, [_first_control()])


def test_this_test_file_is_first_added_before_every_later_phase42_record():
    # Only the FIRST add: a later fix to this file must not redden the guard forever.
    mine = _first_add(THIS)
    for record in _later_records():
        assert _strictly_before(mine, _first_add(record)), record
    # NON-VACUITY (natural RED): the same check against a control record is False.
    assert not _strictly_before(mine, _first_add(_first_control()))


# =================================================================================================
# (4) NOTHING TYPED, KWARGS ONLY FROM THE PRE-REGISTERED BUILDER, CENSUS.
# =================================================================================================


def _typed_numbers(source):
    constants = [n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Constant)]
    assert constants, "meta-guard: no Constant node, the literal walk is vacuous"
    return [n.lineno for n in constants if isinstance(n.value, (int, float, complex))]


def test_no_number_is_typed_in_the_threshold_file(tmp_path):
    source = (_ROOT / THRESHOLD).read_text(encoding="utf-8")
    assert _typed_numbers(source) == []
    planted = _planted(tmp_path, source, source + "\nTHRESHOLD = 0.55\n", "typed.py")
    assert _typed_numbers(planted)


def _fill_kwarg_failures(source):
    calls = [
        n
        for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "fill"
    ]
    slots = [c.args[0].value for c in calls if c.args and isinstance(c.args[0], ast.Constant)]
    failures = [] if slots == [SLOT] else [f"fills {slots}"]
    for call in calls:
        kw = call.keywords[0] if len(call.keywords) == 1 else None
        value = getattr(kw, "value", None)
        if not (
            kw is not None
            and kw.arg is None
            and len(call.args) == 1
            and isinstance(value, ast.Call)
            and not value.args
            and not value.keywords
            and ast.unparse(value.func) == "phase42_prereg.threshold_fill_inputs"
        ):
            failures.append(f"{SLOT}: not exactly **phase42_prereg.threshold_fill_inputs()")
    return failures


def test_fill_takes_only_the_preregistered_kwargs(tmp_path):
    source = (_ROOT / THRESHOLD).read_text(encoding="utf-8")
    assert _fill_kwarg_failures(source) == []
    planted = source.replace(
        "**phase42_prereg.threshold_fill_inputs()",
        "**phase42_prereg.threshold_fill_inputs(), extra=None",
    )
    assert _fill_kwarg_failures(_planted(tmp_path, source, planted, "kwargs.py")) == [
        f"{SLOT}: not exactly **phase42_prereg.threshold_fill_inputs()"
    ]


def test_phase42_scripts_pass_the_slot_census():
    sources = [
        (p.relative_to(_ROOT).as_posix(), p.read_text(encoding="utf-8"))
        for p in sorted(_SCRIPTS.glob("phase42_*.py"))
    ]
    assert THRESHOLD in dict(sources), "meta-guard: the census would miss the threshold file"
    assert _slot_census_failures(sources) == []
    assert fnmatch.fnmatch(THRESHOLD, phase35_prereg.owner_prereg_glob(SLOT))
    # NON-VACUITY: the same file outside phase 42's fill files reds the census.
    misplaced = [("scripts/phase41_threshold_prereg.py", dict(sources)[THRESHOLD])]
    assert any("outside its owner" in f for f in _slot_census_failures(misplaced))


# =================================================================================================
# (5) PITFALL 6: THE FLOAT COMPARISON AGAINST THE EXACT RATIONAL, ENUMERATED AND DECLARED.
# =================================================================================================


def test_exact_disagreements_are_enumerated(threshold):
    fill = threshold.E3_RECALL_THRESHOLD
    found = {}
    for recipe in phase42_prereg.RECIPES:
        value = fill[phase42_prereg.recipe_key(recipe)]
        if value == phase29_prereg.REFUSED:
            continue
        counts = _control_counts(recipe)
        found[phase42_prereg.recipe_tag(recipe)] = {
            leg: phase42_prereg.exact_disagreements(value[leg], counts[leg], counts[leg][1])
            for leg in LEGS
        }
    assert found == _DECLARED_DISAGREEMENTS
    assert found, "meta-guard: no learnable recipe, the enumeration is vacuous"
    # NON-VACUITY: a float threshold moved off the exact rational disagrees at k = n (n / n = 1
    # clears the exact F_Y x ck / cn <= 1 but never the float threshold + 1 > 1).
    recipe = next(r for r in phase42_prereg.RECIPES if phase42_prereg.recipe_tag(r) in found)
    control = _control_counts(recipe)["taught"]
    moved = fill[phase42_prereg.recipe_key(recipe)]["taught"] + 1
    assert control[1] in phase42_prereg.exact_disagreements(moved, control, control[1])


def test_no_skips_in_this_file(tmp_path):
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert _skip_failures(source) == []
    planted = source + '\n\ndef test_planted():\n    pytest.skip("x")\n'
    assert _skip_failures(_planted(tmp_path, source, planted, "skip.py"))
