"""Plan 38-05: the e5_set_sizes fill (RANK-01, D-07/D-08/D-09/D-31), CPU-only.

What this file proves:
- scripts/phase38_sizes_prereg.py declares one maximum set per slot for all eight slots, each size
  read from the committed minting record through phase38_prereg.max_set_size, equal to the
  record's own max_set_size, never typed;
- the declared sizes fit the committed Phase 36 E5 caps (sets and max_set_size, never prefixes);
- it is committed after the minting record and before every other results/phase38_* record
  (Phase 35 legs (a)/(b)), types no size and never passes prefixes to the caps check;
- the file imports only json, pathlib and three torch-free modules, and importing it opens no
  checkpoint (tests/test_phase36_caps.py exec's it on ubuntu CI). It is not torch-free: the
  module-level caps call reaches torch through phase35_prereg.seed_list (38-05 false premise).

It reads only tracked files and git history and writes nothing under results/.
"""

import ast
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
import phase36_caps  # noqa: E402  (same)
import phase38_prereg  # noqa: E402  (same)

from test_phase29_prereg import _assert_frozen_before, _git, _planted  # noqa: E402
from test_phase36_prereg import _HEAVY, _skip_failures  # noqa: E402
from test_phase38_prereg import _first_add, _phase38_records, _strictly_before  # noqa: E402

SIZES = "scripts/phase38_sizes_prereg.py"


@pytest.fixture(scope="module")
def sizes():
    import phase38_sizes_prereg

    return phase38_sizes_prereg


def _minting():
    return json.loads((_ROOT / phase38_prereg.MINTING_RECORD).read_text(encoding="utf-8"))


# =================================================================================================
# (1) THE SIZES ARE THE RECORD'S (D-07, D-09, D-31).
# =================================================================================================


def test_sizes_are_read_from_the_committed_minting_record(sizes):
    slots = _minting()["slots"]
    expected = {s: phase38_prereg.max_set_size(slots[s]["n_cleared"]) for s in phase38_prereg.SLOTS}
    assert dict(sizes.E5_SET_SIZES) == expected
    assert tuple(sizes.E5_SET_SIZES) == phase38_prereg.SLOTS
    assert len(sizes.E5_SET_SIZES) == len(phase38_prereg.SLOTS) == 8
    for slot, size in sizes.E5_SET_SIZES.items():
        assert size == slots[slot]["max_set_size"], slot
    cap = phase35_prereg.ENTRIES["e5_max_set_size"]["value"]
    assert sizes.E5_SET_SIZES["birth_year"] == slots["birth_year"]["n_cleared"] + 1 < cap
    assert [s for s, v in sizes.E5_SET_SIZES.items() if v == cap] == [
        s for s in phase38_prereg.SLOTS if s != "birth_year"
    ]
    assert sizes.MINTING_RECORD in sizes._DERIVATION["source"]


def test_sizes_fit_the_committed_caps_without_prefixes(sizes):
    counts = phase36_caps.counts_for("e5_set_sizes", sizes.E5_SET_SIZES)
    assert phase36_caps.check_unit_caps("E5", **counts) == {
        "sets": len(phase38_prereg.SLOTS),
        "max_set_size": phase35_prereg.ENTRIES["e5_max_set_size"]["value"],
    }
    assert "prefixes" not in counts


def _own_imports(source):
    """Every module name the source imports, anywhere in it."""
    names = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            names.add(node.module)
    return names


def test_the_sizes_file_imports_only_json_pathlib_and_three_torch_free_modules(tmp_path):
    # Truth 4 as planned ("imports torch-free") is false: the module-level D-23 caps call reaches
    # phase35_prereg.seed_list -> phase23_run -> teach_persona -> torch, like the analog
    # phase36_budget_prereg. What the file itself imports is checked here; torch arrives only
    # through phase36_caps.committed_budget.
    source = (_ROOT / SIZES).read_text(encoding="utf-8")
    allowed = {"json", "pathlib", "phase35_prereg", "phase36_caps", "phase38_prereg"}
    assert _own_imports(source) == allowed
    assert not allowed & set(_HEAVY)
    planted = _planted(tmp_path, source, source + "\nimport teach_persona\n", "imports.py")
    assert _own_imports(planted) - allowed == {"teach_persona"}


_OPEN_PROBE = """
import json, os, pathlib, sys
sys.path[:0] = ['scripts', 'src']
seen = []
def hook(event, args):
    if event == 'open' and args and isinstance(args[0], (str, bytes, os.PathLike)):
        path = os.fsdecode(args[0])
        if 'checkpoints' in pathlib.PurePath(path).parts or path.endswith(('.pt', '.safetensors')):
            seen.append(path)
sys.addaudithook(hook)
import phase38_sizes_prereg
{planted}
print(json.dumps(seen))
"""


def _checkpoint_opens(planted=""):
    out = subprocess.run(
        [sys.executable, "-c", _OPEN_PROBE.format(planted=planted)],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_importing_the_sizes_file_opens_no_checkpoint():
    # What tests/test_phase36_caps.py needs on ubuntu CI, where no checkpoint exists: a fresh
    # process imports the file (exit 0) and the open audit hook sees no checkpoints/, .pt or
    # .safetensors path.
    assert _checkpoint_opens() == []
    # NON-VACUITY: the same hook sees a planted checkpoint open (the open fails; the event fires).
    planted = "try:\n    open('checkpoints/planted.pt')\nexcept OSError:\n    pass"
    assert _checkpoint_opens(planted) == ["checkpoints/planted.pt"]


# =================================================================================================
# (2) ORDERING (Phase 35 legs (a)/(b), T-38-20): after the minting record, before every other
# phase-38 record. Honest at zero scoring records and after them.
# =================================================================================================


def _first_commit(path):
    return _git("log", "--format=%H", "--", path).split()[-1]


def _scoring_records():
    return [p for p in _phase38_records() if p != phase38_prereg.MINTING_RECORD]


def test_minting_record_precedes_the_sizes_file():
    minting = _first_add(phase38_prereg.MINTING_RECORD)
    assert _strictly_before(minting, _first_commit(SIZES))
    # NON-VACUITY (natural RED): the reverse relation is False.
    assert not _strictly_before(_first_commit(SIZES), minting)


def test_sizes_file_is_frozen_before_every_other_phase38_record():
    _assert_frozen_before(SIZES, _scoring_records())
    # NON-VACUITY (natural RED): the sizes file was committed after the minting record.
    with pytest.raises(subprocess.CalledProcessError):
        _assert_frozen_before(SIZES, [phase38_prereg.MINTING_RECORD])


def test_this_test_file_is_first_added_before_every_scoring_record():
    # Only the FIRST add: a later fix to this file must not redden the guard forever.
    mine = _first_add("tests/test_phase38_sizes_prereg.py")
    for record in _scoring_records():
        assert _strictly_before(mine, _first_add(record)), record
    # NON-VACUITY: the same check against the minting record (added before this file) is False.
    assert not _strictly_before(mine, _first_add(phase38_prereg.MINTING_RECORD))


# =================================================================================================
# (3) NOTHING TYPED, NO PREFIXES IN THE CAPS CALL (T-38-21, T-38-22), ZERO SKIPS.
# =================================================================================================

_TYPED = {512, 220, 2048}


def _typed_sizes(source):
    constants = [n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Constant)]
    assert constants, "meta-guard: no Constant node, the literal walk is vacuous"
    return [
        n.lineno
        for n in constants
        if type(n.value) is int and n.value in _TYPED  # str docstrings never match
    ]


def test_no_size_is_typed(tmp_path):
    source = (_ROOT / SIZES).read_text(encoding="utf-8")
    assert _typed_sizes(source) == []
    assert _typed_sizes(_planted(tmp_path, source, source + "\nX = 220\n", "typed.py"))


def _caps_call_failures(source):
    calls = [
        n
        for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "check_unit_caps"
    ]
    if len(calls) != 1:
        return [f"{len(calls)} check_unit_caps calls, expected exactly one"]
    (call,) = calls
    failures = [f"keyword {k.arg}=" for k in call.keywords if k.arg == "prefixes"]
    starred = [k.value for k in call.keywords if k.arg is None]
    if not any(
        isinstance(v, ast.Call)
        and isinstance(v.func, ast.Attribute)
        and v.func.attr == "counts_for"
        for v in starred
    ):
        failures.append("no **counts_for(...) argument")
    return failures


def test_caps_call_never_passes_prefixes(tmp_path):
    source = (_ROOT / SIZES).read_text(encoding="utf-8")
    assert _caps_call_failures(source) == []
    planted = source.replace("E5_SET_SIZES))", "E5_SET_SIZES), prefixes=8)")
    assert _caps_call_failures(_planted(tmp_path, source, planted, "prefixes.py")) == [
        "keyword prefixes="
    ]


def test_no_skips_in_this_file(tmp_path):
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert _skip_failures(source) == []
    planted = source + '\n\ndef test_planted():\n    pytest.skip("x")\n'
    assert _skip_failures(_planted(tmp_path, source, planted, "skip.py"))
