"""Plan 41-13: the e1_condition_a_floors and e1_condition_c_band_inputs fills (ERASE-06, ERASE-09),
CPU-only.

What this file proves:
- scripts/phase41_floors_prereg.py fills condition (a)'s floor for every (target, ordering, seed)
  from its committed (ordering, seed) calibration record, by the rule's own route (the record's
  draws through phase19_erasure.per_fact_rows over CORPUS_TIERS, lock_erasure_floor), and condition
  (c)'s band for every (seed, ordering) as mitigation_gate.dialogue_gap_band of the committed
  band-input record's control gap and Phase 40's gap noise floor; nothing typed;
- every consumed path is named in its derivation's source;
- the file imports only pathlib, sys, phase35_prereg and phase41_prereg, and importing it opens no
  checkpoint or data/ file (tests/test_phase36_caps.py exec's it on a CPU-only clone);
- it is committed after every declared input and before every other results/phase41_* record
  (Phase 35 legs (a)/(b)), and both fills live in this one file (red case b7_41).

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

import phase35_prereg  # noqa: E402  (scripts/ is not a package)
import phase41_prereg  # noqa: E402  (same)

from test_phase29_prereg import _assert_frozen_before, _git, _planted  # noqa: E402
from test_phase35_prereg import _slot_census_failures  # noqa: E402
from test_phase36_prereg import _skip_failures  # noqa: E402
from test_phase41_prereg import (  # noqa: E402
    _first_add,
    _opens_a_checkpoint,
    _phase41_records,
    _strictly_before,
)

FLOORS = "scripts/phase41_floors_prereg.py"
THIS = "tests/test_phase41_floors_prereg.py"


@pytest.fixture(scope="module")
def floors():
    import phase41_floors_prereg

    return phase41_floors_prereg


def _read(rel):
    return json.loads((_ROOT / rel).read_text(encoding="utf-8"))


def _tracked(rel):
    return _git("ls-files", "--", rel) == rel


# =================================================================================================
# (1) THE VALUES ARE THE COMMITTED RECORDS' (ERASE-06, ERASE-09).
# =================================================================================================


def test_floors_are_computed_from_the_committed_records(floors):
    import phase18_extraction
    import phase19_erasure

    fill = floors.E1_CONDITION_A_FLOORS
    targets, orderings, seeds = (
        phase41_prereg.TARGETS,
        phase41_prereg.ORDERINGS,
        phase41_prereg.SEEDS,
    )
    assert set(fill) == {(t, o, s) for t in targets for o in orderings for s in seeds}
    fact = phase19_erasure.select_calibration_fact()
    values = {fact.id: fact.value}
    for (target, ordering, seed), row in fill.items():
        path = phase41_prereg.calibration_record(ordering, seed)
        assert row["calibration_record"] == path
        assert _tracked(path), path
        record = _read(path)
        successes = questions = 0
        for tier in phase18_extraction.CORPUS_TIERS:
            rows = phase19_erasure.per_fact_rows(
                record["draws"], values, family=record["family"], tier=tier
            )
            successes += rows[fact.id]["n_answerable"]
            questions += rows[fact.id]["n_questions"]
        rate = successes / questions
        assert row["calibration_rate"] == rate, (target, ordering, seed)
        assert row["floor"] == phase19_erasure.lock_erasure_floor(rate), (target, ordering, seed)
        assert row["floor_branch"] == phase19_erasure.floor_branch(rate), (target, ordering, seed)


def test_bands_are_the_d01_band_of_the_records(floors):
    import mitigation_gate

    bands = floors.E1_CONDITION_C_BAND_INPUTS
    seeds, orderings = phase41_prereg.SEEDS, phase41_prereg.ORDERINGS
    assert set(bands) == {(s, o) for s in seeds for o in orderings}
    assert _tracked(phase41_prereg.NOISE_FLOOR_RECORD)
    gap_noise_floor = _read(phase41_prereg.NOISE_FLOOR_RECORD)["gap_noise_floor"]
    for (seed, ordering), band in bands.items():
        path = phase41_prereg.band_record(seed, ordering)
        assert _tracked(path), path
        record = _read(path)
        assert (record["seed"], record["ordering"]) == (seed, ordering)
        assert band == mitigation_gate.dialogue_gap_band(
            control_gap=record["control_gap"], gap_noise_floor=gap_noise_floor
        ), (seed, ordering)


def test_every_consumed_path_is_in_its_derivation_source():
    builders = (phase41_prereg.floors_fill_inputs(), phase41_prereg.band_fill_inputs())
    prep = len(phase41_prereg.SEEDS) * len(phase41_prereg.ORDERINGS)
    assert [len(b["input_records"]) for b in builders] == [prep + 1, prep + 1]
    for inputs in builders:
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


def test_the_floors_file_imports_only_pathlib_sys_and_the_two_preregs(tmp_path):
    source = (_ROOT / FLOORS).read_text(encoding="utf-8")
    allowed = {"pathlib", "sys", "phase35_prereg", "phase41_prereg"}
    assert _own_imports(source) == allowed
    planted = _planted(tmp_path, source, source + "\nimport phase19_erasure\n", "imports.py")
    assert _own_imports(planted) - allowed == {"phase19_erasure"}


_PROBE = """
import importlib.util, json, os, pathlib, sys

{predicate}

_REPO = pathlib.Path(sys.argv[1]).resolve()
_FLAGGED = []


def _hook(event, args):
    if event == "open" and args and _opens_a_checkpoint(args[0], _REPO):
        _FLAGGED.append(os.fspath(args[0]))


sys.addaudithook(_hook)
spec = importlib.util.spec_from_file_location("phase41_floors_prereg", _REPO / sys.argv[2])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

imported = list(_FLAGGED)
_FLAGGED.clear()
planted = [_REPO / "checkpoints" / "planted", _REPO / "data" / "planted"]
for path in planted:
    try:
        open(path, encoding="utf-8")
    except FileNotFoundError:
        pass
print(json.dumps({{
    "import_flagged": imported,
    "safetensors_loaded": "safetensors" in sys.modules,
    "keys": [len(module.E1_CONDITION_A_FLOORS), len(module.E1_CONDITION_C_BAND_INPUTS)],
    "planted": [os.fspath(p) for p in planted],
    "planted_flagged": list(_FLAGGED),
}}))
"""


def test_importing_the_floors_file_opens_no_checkpoint():
    # A fresh process with no scripts/ on sys.path loads the file by path: its own sys.path
    # inserts must reach both preregs, and the open audit hook sees no checkpoints/ or data/ path.
    script = _PROBE.format(predicate=inspect.getsource(_opens_a_checkpoint))
    out = subprocess.run(
        [sys.executable, "-c", script, str(_ROOT), FLOORS],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    result = json.loads(out.stdout.strip().splitlines()[-1])
    assert result["import_flagged"] == []
    assert result["safetensors_loaded"] is False
    prep = len(phase41_prereg.SEEDS) * len(phase41_prereg.ORDERINGS)
    assert result["keys"] == [len(phase41_prereg.TARGETS) * prep, prep]
    # NON-VACUITY: one planted open per directory branch, each flagged by the same hook.
    assert result["planted_flagged"] == result["planted"]


# =================================================================================================
# (3) ORDERING (Phase 35 legs (a)/(b), T-41-50): after every declared input, before every other
# results/phase41_* record. Honest at zero cell records and after them.
# =================================================================================================


def _first_commit(path):
    return _git("log", "--format=%H", "--", path).split()[-1]


def _declared_inputs():
    return sorted(
        {
            *phase41_prereg.floors_fill_inputs()["input_records"],
            *phase41_prereg.band_fill_inputs()["input_records"],
        }
    )


def _is_prep(path):
    return any(
        fnmatch.fnmatch(path, glob)
        for glob in (phase41_prereg.CALIBRATION_GLOB, phase41_prereg.BAND_GLOB)
    )


def _later_records():
    return [p for p in _phase41_records() if not _is_prep(p)]


def _first_calibration():
    return phase41_prereg.calibration_record(phase41_prereg.ORDERINGS[0], phase41_prereg.SEEDS[0])


def test_every_declared_input_precedes_the_floors_file():
    first = _first_commit(FLOORS)
    inputs = _declared_inputs()
    prep = len(phase41_prereg.SEEDS) * len(phase41_prereg.ORDERINGS)
    assert len(inputs) == 2 * prep + 2
    for path in inputs:
        assert _strictly_before(_first_add(path), first), path
    # NON-VACUITY (natural RED): the reverse relation is False for every input.
    assert not any(_strictly_before(first, _first_add(path)) for path in inputs)


def test_floors_file_is_frozen_before_every_later_phase41_record():
    prep = [p for p in _phase41_records() if _is_prep(p)]
    assert len(prep) == 2 * len(phase41_prereg.SEEDS) * len(phase41_prereg.ORDERINGS)
    _assert_frozen_before(FLOORS, _later_records())
    # NON-VACUITY (natural RED): the floors file was committed after the calibration records.
    with pytest.raises(subprocess.CalledProcessError):
        _assert_frozen_before(FLOORS, [_first_calibration()])


def test_this_test_file_is_first_added_before_every_later_phase41_record():
    # Only the FIRST add: a later fix to this file must not redden the guard forever.
    mine = _first_add(THIS)
    for record in _later_records():
        assert _strictly_before(mine, _first_add(record)), record
    # NON-VACUITY (natural RED): the same check against a calibration record is False.
    assert not _strictly_before(mine, _first_add(_first_calibration()))


# =================================================================================================
# (4) NOTHING TYPED, KWARGS ONLY FROM THE PRE-REGISTERED BUILDERS, CENSUS, ZERO SKIPS.
# =================================================================================================


def _typed_numbers(source):
    constants = [n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Constant)]
    assert constants, "meta-guard: no Constant node, the literal walk is vacuous"
    return [n.lineno for n in constants if isinstance(n.value, (int, float, complex))]


def test_no_number_is_typed_in_the_floors_file(tmp_path):
    source = (_ROOT / FLOORS).read_text(encoding="utf-8")
    assert _typed_numbers(source) == []
    planted = _planted(tmp_path, source, source + "\nFLOOR = 0.09\n", "typed.py")
    assert _typed_numbers(planted)


_BUILDERS = {
    "e1_condition_a_floors": "floors_fill_inputs",
    "e1_condition_c_band_inputs": "band_fill_inputs",
}


def _fill_kwarg_failures(source):
    calls = [
        n
        for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "fill"
    ]
    slots = [c.args[0].value for c in calls if c.args and isinstance(c.args[0], ast.Constant)]
    failures = [] if sorted(slots) == sorted(_BUILDERS) else [f"fills {slots}"]
    for call, slot in zip(calls, slots):
        kw = call.keywords[0] if len(call.keywords) == 1 else None
        value = getattr(kw, "value", None)
        if not (
            kw is not None
            and kw.arg is None
            and len(call.args) == 1
            and isinstance(value, ast.Call)
            and not value.args
            and not value.keywords
            and ast.unparse(value.func) == f"phase41_prereg.{_BUILDERS.get(slot)}"
        ):
            failures.append(f"{slot}: not exactly **phase41_prereg.{_BUILDERS.get(slot)}()")
    return failures


def test_fills_take_only_the_preregistered_kwargs(tmp_path):
    source = (_ROOT / FLOORS).read_text(encoding="utf-8")
    assert _fill_kwarg_failures(source) == []
    planted = source.replace(
        "**phase41_prereg.band_fill_inputs()", "**phase41_prereg.band_fill_inputs(), extra=None"
    )
    assert _fill_kwarg_failures(_planted(tmp_path, source, planted, "kwargs.py")) == [
        "e1_condition_c_band_inputs: not exactly **phase41_prereg.band_fill_inputs()"
    ]


def test_phase41_scripts_pass_the_slot_census():
    sources = [
        (p.relative_to(_ROOT).as_posix(), p.read_text(encoding="utf-8"))
        for p in sorted(_SCRIPTS.glob("phase41_*.py"))
    ]
    assert FLOORS in dict(sources), "meta-guard: the census would miss the floors file"
    assert _slot_census_failures(sources) == []
    for slot in _BUILDERS:
        assert fnmatch.fnmatch(FLOORS, phase35_prereg.owner_prereg_glob(slot))
    # NON-VACUITY: the same file outside phase 41's fill files reds the census.
    misplaced = [*sources, ("scripts/phase42_floors_prereg.py", dict(sources)[FLOORS])]
    assert _slot_census_failures(misplaced)


def test_no_skips_in_this_file(tmp_path):
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert _skip_failures(source) == []
    planted = source + '\n\ndef test_planted():\n    pytest.skip("x")\n'
    assert _skip_failures(_planted(tmp_path, source, planted, "skip.py"))
