"""Plan 36-02 Task 1: the D-09 unit caps (scripts/phase36_caps.py), CPU-only.

What this file proves:
- check_unit_caps passes at a cap and refuses one over it, an unknown front and an unknown cap name;
- prove_budget_shape re-proves the v6.0 budget contract locally (exact fsum, the front set, finite
  non-negative hours, an int S, a complete unit_caps block) and refuses each break;
- committed_budget reads only the COMMITTED budget record and refuses while it is untracked;
- owner_overruns names every over-cap owner value; the real repo's owner fill files are scanned
  (honest-green at zero), and a planted repo with an over-cap grid reds;
- the module imports without torch and every function has a CPU test.

It writes nothing under results/.
"""

import ast
import json
import math
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

import phase30_points  # noqa: E402  (scripts/ is not a package)
import phase35_prereg  # noqa: E402  (same)
import phase36_caps  # noqa: E402  (same)

from test_phase35_prereg import _fill_sites, _git_in, _planted_repo  # noqa: E402
from test_phase36_prereg import _untested_functions  # noqa: E402

CAPS = "scripts/phase36_caps.py"


def _caps():
    return {front: dict.fromkeys(names, 4) for front, names in phase36_caps.CAP_FIELDS.items()}


def _budget(**overrides):
    """A planted budget: hours are multiples of 0.5, so their fsum is exact."""
    front_hours = {
        "probes": 2.0,
        "R1b": 1.5,
        "E1": 10.0,
        "E2": 8.0,
        "E3": 12.0,
        "E4": 5.0,
        "E5": 6.0,
        "E6": 4.5,
    }
    caps = _caps()
    caps["E1"]["checkpoints_per_cell"] = 5
    caps["E2"]["seeds"] = 5
    record = {
        "front_hours": front_hours,
        "total_hours": math.fsum(front_hours.values()),
        "stop_line_hours": 73.5,
        "e2_seed_count": 5,
        "unit_caps": caps,
        "unit_prices": {"e4_point_seconds": 6000.0},
    }
    record.update(overrides)
    return record


@pytest.fixture
def committed(monkeypatch):
    """Route committed_budget's read to a planted record (the real one does not exist yet)."""
    record = _budget()

    def read(rel, tracked, what):
        assert rel == phase36_caps.BUDGET_RECORD and rel in tracked, (rel, what)
        return json.loads(json.dumps(record))

    monkeypatch.setattr(phase30_points, "_tracked_json", read)
    return [phase36_caps.BUDGET_RECORD]


# =================================================================================================
# (1) THE NAMES.
# =================================================================================================


def test_names_resolve_from_the_v6_registry():
    assert phase36_caps.BUDGET_RECORD == "results/phase36_budget.json"
    assert phase36_caps.BUDGET_RECORD in phase35_prereg.V6_RESULT_PATHS
    assert set(phase36_caps.CAP_FIELDS) == {"E1", "E2", "E3", "E4", "E5", "E6"}
    assert set(phase36_caps.CAP_FIELDS) < set(phase35_prereg.V6_MPS_FRONTS)
    assert set(phase36_caps.SLOT_COUNTS) <= set(phase35_prereg.SLOTS)
    owners = {s: phase35_prereg.SLOTS[s]["owner_phase"] for s in phase36_caps.SLOT_COUNTS}
    assert owners == {
        "e1_checkpoint_grid": 41,
        "e3_grid_subset": 42,
        "e5_set_sizes": 38,
        "e6_entry_subset": 39,
    }
    for front in phase36_caps.SLOT_COUNTS.values():
        assert front in phase36_caps.CAP_FIELDS
    with pytest.raises(TypeError):
        phase36_caps.CAP_FIELDS["E9"] = ()
    with pytest.raises(SystemExit, match=r"^\[phase36_caps\] x$"):
        phase36_caps._prove(False, "x")


def test_tracked_files_is_git_ls_files():
    tracked = phase36_caps.tracked_files()
    assert isinstance(tracked, list)
    assert "scripts/phase35_prereg.py" in tracked
    assert tracked == sorted(set(tracked), key=tracked.index)  # one line per path
    assert [phase36_caps._is_count(v) for v in (0, 3, -1, True, 1.0)] == [
        True,
        True,
        False,
        False,
        False,
    ]


# =================================================================================================
# (2) THE BUDGET SHAPE (re-proved locally; never phase35_prereg's private helpers).
# =================================================================================================


def test_prove_budget_shape_accepts_the_contract():
    record = _budget()
    assert phase36_caps.prove_budget_shape(record) is record


def _broken():
    good = _budget()
    hours = good["front_hours"]
    yield "total", {**good, "total_hours": good["total_hours"] + 1e-12}
    yield "fronts", {**good, "front_hours": {k: v for k, v in hours.items() if k != "E6"}}
    yield "negative", {**good, "front_hours": {**hours, "E6": -0.5}}
    yield "nonfinite", {**good, "front_hours": {**hours, "E6": math.inf}}
    yield "bool S", {**good, "e2_seed_count": True}
    yield "S low", {**good, "e2_seed_count": 1}
    yield "S high", {**good, "e2_seed_count": len(phase35_prereg.seed_list()) + 1}
    yield "stop line", {**good, "stop_line_hours": good["total_hours"] - 0.5}
    yield "ceiling", {**good, "stop_line_hours": 90.5}
    yield "missing field", {k: v for k, v in good.items() if k != "stop_line_hours"}
    caps = _caps()
    del caps["E5"]["prefixes"]
    yield "missing cap", {**good, "unit_caps": caps}
    caps = _caps()
    del caps["E6"]
    yield "missing front caps", {**good, "unit_caps": caps}
    caps = _caps()
    caps["E3"]["recipes"] = True
    yield "bool cap", {**good, "unit_caps": caps}
    caps = _caps()
    caps["E3"]["recipes"] = -1
    yield "negative cap", {**good, "unit_caps": caps}
    caps = _caps()
    caps["E2"]["seeds"] = 4
    yield "seeds != S", {**good, "unit_caps": caps}
    yield "not a mapping", [good]


@pytest.mark.parametrize("label", [label for label, _ in _broken()])
def test_prove_budget_shape_refuses(label):
    record = dict(_broken())[label]
    with pytest.raises(SystemExit, match=r"^\[phase36_caps\]"):
        phase36_caps.prove_budget_shape(record)


def test_committed_budget_refuses_an_untracked_record():
    # State-independent since 36-08 committed the record: untracked is simulated by the listing.
    tracked = [p for p in phase36_caps.tracked_files() if p != phase36_caps.BUDGET_RECORD]
    with pytest.raises(SystemExit, match="not TRACKED"):
        phase36_caps.committed_budget(tracked)


def test_committed_budget_reads_through_tracked_json(committed):
    record = phase36_caps.committed_budget(committed)
    assert record["unit_caps"]["E1"]["checkpoints_per_cell"] == 5


# =================================================================================================
# (3) check_unit_caps (D-09, T-36-08).
# =================================================================================================


def test_check_unit_caps_at_and_over_the_cap(committed):
    assert phase36_caps.check_unit_caps("E1", tracked=committed, checkpoints_per_cell=5) == {
        "checkpoints_per_cell": 5
    }
    with pytest.raises(SystemExit) as refused:
        phase36_caps.check_unit_caps("E1", tracked=committed, checkpoints_per_cell=6)
    message = str(refused.value)
    for part in ("E1", "checkpoints_per_cell", "6", "5", "D-09: exceeding a Phase 36 cap"):
        assert part in message, part


@pytest.mark.parametrize(
    ("front", "counts", "pattern"),
    [
        ("E9", {"cells": 1}, "front 'E9'"),
        ("R1b", {"cells": 1}, "front 'R1b'"),
        ("E1", {"bogus": 1}, "bogus"),
        ("E1", {"cells": True}, "not an int"),
        ("E1", {"cells": -1}, "not an int"),
        ("E1", {}, "no count"),
    ],
)
def test_check_unit_caps_refuses_unknown_names(committed, front, counts, pattern):
    with pytest.raises(SystemExit, match=pattern):
        phase36_caps.check_unit_caps(front, tracked=committed, **counts)


# =================================================================================================
# (4) THE OWNER SCAN (D-09): counts_for, owner_overruns, the real repo, a planted repo.
# =================================================================================================


def _cell(lr, steps, batch, sigma):
    return {"recipe": {"lr": lr, "steps": steps, "batch": batch}, "sigma": sigma}


def test_counts_for_each_slot():
    assert phase36_caps.counts_for("e1_checkpoint_grid", {"checkpoints": (1, 4, 9)}) == {
        "checkpoints_per_cell": 3
    }
    cells = tuple(
        _cell(lr, steps, 16, sigma)
        for lr, steps in ((1e-3, 200), (5e-4, 800))
        for sigma in phase35_prereg.E3_SIGMAS
    )
    assert phase36_caps.counts_for("e3_grid_subset", {"cells": cells}) == {
        "recipes": 2,
        "max_steps": 800,
        "max_batch": 16,
    }
    assert phase36_caps.counts_for("e5_set_sizes", {"a": 12, "b": 40}) == {
        "sets": 2,
        "max_set_size": 40,
    }
    assert phase36_caps.counts_for("e6_entry_subset", (0, 3, 7)) == {"entries": 3}
    with pytest.raises(SystemExit, match="e4_parameters"):
        phase36_caps.counts_for("e4_parameters", {})


def test_owner_overruns_names_each_overrun():
    record = _budget()
    assert phase36_caps.owner_overruns({}, record) == []
    assert (
        phase36_caps.owner_overruns(
            {"e1_checkpoint_grid": {"checkpoints": (1, 2, 3, 4, 5)}, "e6_entry_subset": (1, 2)},
            record,
        )
        == []
    )
    failures = phase36_caps.owner_overruns(
        {"e1_checkpoint_grid": {"checkpoints": tuple(range(1, 7))}, "e5_set_sizes": {"a": 9}},
        record,
    )
    assert len(failures) == 2
    assert "checkpoints_per_cell" in failures[0] and "6" in failures[0]
    assert "max_set_size" in failures[1] and "9" in failures[1]


def _owner_values(run, root):
    """``{slot: bound value}`` for every tracked owner fill file of a SLOT_COUNTS slot."""
    import importlib.util

    values = {}
    for path, slots in sorted(_fill_sites(run).items()):
        for slot in sorted(slots & set(phase36_caps.SLOT_COUNTS)):
            spec = importlib.util.spec_from_file_location(pathlib.Path(path).stem, root / path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            values[slot] = getattr(module, slot.upper())
    return values


def test_owner_fill_files_respect_the_caps_on_the_real_repo():
    values = _owner_values(_git_in(_ROOT), _ROOT)
    if values:
        assert phase36_caps.owner_overruns(values, phase36_caps.committed_budget()) == []
    else:
        # 0 today is honest-green; live when Phases 38/39/41/42 land. No owner fill file can
        # exist before plan 08's budget, so there is no cap to read yet.
        assert phase36_caps.owner_overruns(values, {"unit_caps": {}}) == []


def test_owner_scan_reds_on_a_planted_over_cap_file(tmp_path):
    caps = _caps()
    caps["E1"]["checkpoints_per_cell"] = 2
    caps["E2"]["seeds"] = 5
    planted_budget = _budget(unit_caps=caps)
    owner = (
        "import phase35_prereg\n"
        'E1_CHECKPOINT_GRID = phase35_prereg.fill("e1_checkpoint_grid", checkpoints=(1, 2, 3))\n'
    )
    run = _planted_repo(
        tmp_path / "repo",
        [
            [(phase36_caps.BUDGET_RECORD, json.dumps(planted_budget))],
            [("scripts/phase41_prereg.py", owner)],
        ],
    )
    assert _fill_sites(run) == {"scripts/phase41_prereg.py": frozenset({"e1_checkpoint_grid"})}
    budget = phase36_caps.prove_budget_shape(
        json.loads(run("show", f"HEAD:{phase36_caps.BUDGET_RECORD}").stdout)
    )
    over = phase36_caps.owner_overruns({"e1_checkpoint_grid": {"checkpoints": (1, 2, 3)}}, budget)
    assert len(over) == 1 and "checkpoints_per_cell" in over[0]
    in_cap = {"e1_checkpoint_grid": {"checkpoints": (1, 2)}}
    assert phase36_caps.owner_overruns(in_cap, budget) == []


# =================================================================================================
# (5) CPU-ONLY AT IMPORT; EVERY FUNCTION HAS A CPU TEST; NO PRIVATE phase35_prereg ACCESS.
# =================================================================================================

_HEAVY = ("torch", "teach_persona", "phase19_erasure", "phase18_extraction", "phase23_run")


def test_the_caps_module_imports_without_torch():
    probe = (
        "import sys; sys.path.insert(0, 'scripts'); import phase36_caps; "
        f"print(*[name in sys.modules for name in {_HEAVY!r}])"
    )
    out = subprocess.run(
        [sys.executable, "-c", probe], cwd=_ROOT, capture_output=True, text=True, check=True
    )
    assert out.stdout.split() == ["False"] * len(_HEAVY), out.stdout


def test_every_caps_function_has_a_cpu_test():
    source = (_ROOT / CAPS).read_text(encoding="utf-8")
    assert [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)]
    test_source = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert _untested_functions("phase36_caps", source, test_source) == []


def test_no_private_phase35_prereg_access():
    tree = ast.parse((_ROOT / CAPS).read_text(encoding="utf-8"))
    private = [
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "phase35_prereg"
        and node.attr.startswith("_")
    ]
    public = [
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "phase35_prereg"
    ]
    assert public, "meta-guard: no phase35_prereg access found, the walk is blind"
    assert private == []
