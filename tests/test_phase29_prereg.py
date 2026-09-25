"""Plan 29-01: the v5.0 pre-registration, frozen by ancestry and checked against its sources.

What this file proves, CPU-only:
- ancestry: every commit touching scripts/phase29_prereg.py precedes the first-add of every
  tracked results/phase30_* .. phase34_* file (honest-green with none tracked);
- the pathspecs are DERIVED from V5_RESULT_PATHS, disjoint from every v4.0 path, and no
  probe/calibration path parses as a point key;
- the 12 keys wrap phase25_record.point_key, every v4.0 parser refuses them, and leg_keys is the
  D-12 short-circuit set;
- the gate route, F_Y, the grid and the floor-refusal markers are imported by reference (`is`);
- the module imports without torch, and replay_windows is the DP call site's expression;
- control_is_unlearnable agrees with the route's floor refusal on both sides of the boundary,
  and the REFUSED record carries counts, the recipe and the v4.0 adv_n64 reading re-read from the
  frontier;
- no retry/alternate key or name is exposed (D-14).
Nothing here writes under results/: a results/phase3* file would start the ancestry clock.
"""

import ast
import fnmatch
import json
import pathlib
import re
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

import mitigation_budget  # noqa: E402  (scripts/ is not a package)
import mitigation_gate  # noqa: E402  (same)
import phase20_gate_coverage  # noqa: E402  (same)
import phase25_condition_c  # noqa: E402  (same)
import phase25_promotion  # noqa: E402  (same)
import phase25_record  # noqa: E402  (same)
import phase27_prereg  # noqa: E402  (same)
import phase29_prereg  # noqa: E402  (same)

PREREG = "scripts/phase29_prereg.py"
FRONTIER = _ROOT / "results" / "phase25_frontier.json"
# The n64 leg's recipe: key index 7 below is advr_n64_ratio0p250000 (WR-02).
_RECIPE = {"replay_windows": 256, "n_facts": 64, "seed": 1337, "max_steps": 200}


def _git(*args):
    """Run git inside the repository and return its stdout, raising on a non-zero exit."""
    return subprocess.run(
        ("git", *args), cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


@pytest.fixture(scope="module")
def frontier():
    return json.loads(FRONTIER.read_text(encoding="utf-8"))


# =================================================================================================
# (1) ANCESTRY (PREREG-01 SC1, T-29-01).
# =================================================================================================


def _assert_frozen_before(prereg_artifact, tracked):
    """The Phase-18 mould: every commit touching `prereg_artifact` is a STRICT ancestor of the
    earliest add of every path in `tracked`; honest with zero tracked paths."""
    assert _git("rev-parse", "--is-shallow-repository") == "false", (
        "shallow clone: the pre-registration commit objects are absent, so this guard cannot "
        "distinguish 'the ordering holds' from 'the ordering was never checked'. "
        "Set `fetch-depth: 0` on actions/checkout (see .github/workflows/ci.yml)."
    )
    prereg_commits = _git("log", "--format=%H", "--", prereg_artifact).split()
    assert prereg_commits, f"{prereg_artifact} has no commits — green and blind"

    checked = 0
    for artifact in tracked:
        adds = _git("log", "--diff-filter=A", "--format=%H", "--", artifact).split()
        # git log is newest-first, so the commit that ADDED the file is the last entry. Taking the
        # earliest add is what makes a delete-and-re-add cycle unable to launder the ordering.
        first_add = adds[-1]
        for prereg in prereg_commits:
            assert prereg != first_add, (
                f"{prereg_artifact} and {artifact} were committed in the SAME commit {prereg} — "
                "the pre-registration must land STRICTLY BEFORE the artifact it pins, or it is "
                "not a pre-registration at all. `git merge-base --is-ancestor X X` exits 0, so "
                "the ancestry check below cannot see this on its own."
            )
            subprocess.run(
                ("git", "merge-base", "--is-ancestor", prereg, first_add),
                cwd=_ROOT,
                check=True,
            )
            checked += 1

    assert checked == len(prereg_commits) * len(tracked), (
        f"checked {checked} pairs but {len(prereg_commits)} pre-registration commit(s) x "
        f"{len(tracked)} tracked artifact(s) is {len(prereg_commits) * len(tracked)}"
    )
    assert bool(checked) == bool(tracked), (
        f"checked {checked} pair(s) against {len(tracked)} tracked artifact(s) — those disagree"
    )


def test_phase29_prereg_is_frozen_before_every_v5_result():
    tracked = sorted(
        {
            path
            for spec in phase29_prereg.ARTIFACT_PATHSPECS
            for path in _git("ls-files", spec).split()
        }
    )
    _assert_frozen_before(PREREG, tracked)


# =================================================================================================
# (2) PATHS (D-02, D-03).
# =================================================================================================


def test_pathspecs_are_derived_and_cover_results_phase30_to_34():
    p = phase29_prereg
    expected = tuple(f"results/phase3{n}_*" for n in range(5))
    assert p.ARTIFACT_PATHSPECS == expected
    assert p.ARTIFACT_PATHSPECS == tuple(
        sorted({path.split("_", 1)[0] + "_*" for path in p.V5_RESULT_PATHS})
    )
    for path in p.V5_RESULT_PATHS:
        assert any(fnmatch.fnmatch(path, spec) for spec in expected), path


def test_paths_are_distinct_from_every_v4_path():
    tracked = _git("ls-files", "results").split()
    assert tracked, "git ls-files results returned nothing — the disjointness check is blind"
    for path in phase29_prereg.V5_RESULT_PATHS:
        assert not path.startswith("results/phase2"), path
        assert not [t for t in tracked if fnmatch.fnmatch(t, path)], path


def test_no_probe_or_calibration_path_parses_as_a_point_key():
    concrete = [p for p in phase29_prereg.V5_RESULT_PATHS if "*" not in p]
    assert concrete
    keys = phase29_prereg.POINT_KEYS()
    for path in concrete:
        stem = pathlib.PurePosixPath(path).stem.removeprefix("phase32_point_")
        assert stem not in keys, path
        with pytest.raises(SystemExit):
            phase25_record.parse_point_key(stem)


def test_point_record_path_is_proved_against_the_key_set():
    key = phase29_prereg.POINT_KEYS()[0]
    assert phase29_prereg.point_record_path(key) == f"results/phase32_point_{key}.json"
    for bad in ("adv_n8_ratio0p000000", "advr_n8_ratio0p000000/../x", "calibration"):
        with pytest.raises(SystemExit):
            phase29_prereg.point_record_path(bad)


# =================================================================================================
# (3) KEYS (D-01, D-12, D-14).
# =================================================================================================


def test_keys_are_twelve_and_wrap_the_v4_renderer():
    p = phase29_prereg
    keys = p.POINT_KEYS()
    assert len(keys) == len(set(keys)) == len(p.ADVR_ARMS) * len(p.RATIO_GRID) == 12
    assert keys[0] == "advr_n8_ratio0p000000" and keys[-1] == "advr_n64_ratio1p909091"
    rendered = iter(keys)
    for arm in p.ADVR_ARMS:
        twin = arm.replace("advr", "adv", 1)
        for ratio in p.RATIO_GRID:
            key = next(rendered)
            assert key.replace("advr", "adv", 1) == phase25_record.point_key(twin, ratio), key


def test_keys_are_refused_by_every_v4_parser():
    for key in phase29_prereg.POINT_KEYS():
        with pytest.raises(SystemExit):
            phase25_record.parse_point_key(key)
        with pytest.raises(SystemExit):
            phase27_prereg.arm_of(key)


@pytest.mark.parametrize(
    ("arm", "ratio"),
    [("adv_n8", 0.25), ("advr_n8", float("nan")), ("advr_n8", -0.25), ("advr_n16", 0.25)],
)
def test_keys_refuse_foreign_arms_and_bad_ratios(arm, ratio):
    with pytest.raises(SystemExit):
        phase29_prereg.point_key(arm, ratio)


def test_keys_put_each_legs_control_first():
    p = phase29_prereg
    for arm, leg in zip(p.ADVR_ARMS, p.LEGS):
        first = next(k for k in p.POINT_KEYS() if k.startswith(f"{arm}_"))
        assert first == p.control_key(leg) == p.point_key(arm, 0.0)


def test_leg_keys_are_the_d12_short_circuit_set():
    p = phase29_prereg
    joined = ()
    for leg in p.LEGS:
        keys = p.leg_keys(leg)
        assert keys[0] == p.control_key(leg)
        assert len(keys) == len(p.RATIO_GRID)
        assert set(keys) <= set(p.POINT_KEYS())
        assert not set(keys) & set(joined)
        joined += keys
    assert joined == tuple(p.POINT_KEYS())
    with pytest.raises(SystemExit):
        p.leg_keys("n16")
    with pytest.raises(SystemExit):
        p.control_key("n16")


def test_no_retry_or_alternate_key_is_exposed():
    p = phase29_prereg
    keys = set(p.POINT_KEYS())
    pattern = re.compile(r"advr_n\d+_ratio")
    public = [name for name in dir(p) if not name.startswith("_")]
    for name in public:
        value = getattr(p, name)
        strings = (
            [value]
            if isinstance(value, str)
            else [v for v in value if isinstance(v, str)]
            if isinstance(value, tuple)
            else []
        )
        for s in strings:
            if pattern.search(s):
                assert s in keys, (name, s)
    banned = re.compile(r"retry|alternate|rerun|retune", re.IGNORECASE)
    assert not [name for name in public if banned.search(name)]


# =================================================================================================
# (4) BY REFERENCE AND CPU-ONLY (D-05, D-04).
# =================================================================================================


def test_constants_are_by_reference():
    p = phase29_prereg
    assert p.F_Y is mitigation_gate.F_Y
    assert p.RATIO_GRID is mitigation_budget.ADVERSARIAL_RATIO_GRID
    assert p.GATE_ROUTE is phase20_gate_coverage.corrected_point_verdict
    assert p.COVERAGE_FLOOR_REFUSAL_MARKERS is phase25_promotion.COVERAGE_FLOOR_REFUSAL_MARKERS
    assert p.RECORDS_AT_COMMIT == 0


def test_the_prereg_imports_without_torch():
    probe = (
        "import sys; sys.path.insert(0, 'scripts'); import phase29_prereg; "
        "print('torch' in sys.modules, 'teach_persona' in sys.modules)"
    )
    out = subprocess.run(
        [sys.executable, "-c", probe], cwd=_ROOT, capture_output=True, text=True, check=True
    )
    assert out.stdout.split() == ["False", "False"], out.stdout


def test_replay_windows_equal_the_dp_expression():
    import teach_persona  # torch at import — inside the test only

    for n in (8, 64):
        assert (
            phase29_prereg.replay_windows(n)
            == teach_persona.replay_window_budget(n) // teach_persona.BLOCK_SIZE
            == teach_persona.REPLAY_WINDOWS_PER_FACT * n
        )
    assert (phase29_prereg.replay_windows(8), phase29_prereg.replay_windows(64)) == (32, 256)
    for bad in (0, True, 8.0):
        with pytest.raises(SystemExit):
            phase29_prereg.replay_windows(bad)
    resolved = [
        getattr(teach_persona, name.split(".")[1]).parts[-2:]
        for name in phase29_prereg.REPLAY_SOURCE
    ]
    assert resolved == [("data", "dialog_train.bin"), ("data", "dialog_train_mask.bin")]


# =================================================================================================
# (5) THE REFUSAL (D-11, D-12, D-13).
# =================================================================================================


def _route_kwargs(entry):
    """tests/test_phase27_prereg.py's `_route_kwargs` shape."""
    kwargs = {k: entry[k] for k in phase25_promotion.PIN_KWARGS if not k.startswith("sweep_")}
    curve = entry["whole_curve_inputs"]
    kwargs.update({k: curve[k] for k in curve if k.startswith("sweep_")})
    kwargs["retention_floor_provenance"] = {
        "regime": phase20_gate_coverage.ADAPTER_REGIME,
        "seeds": phase25_condition_c.RETENTION_FLOOR_DISCLOSURE["seeds"],
    }
    return kwargs


def test_unlearnable_predicate_agrees_with_the_route(frontier):
    p = phase29_prereg
    kwargs = _route_kwargs(frontier["points"]["adv_n64_ratio0p000000"]["verdict"])
    kwargs["control_taught_recall"] = 1 / 1008

    kwargs["control_heldout_recall"] = 0 / 648
    assert p.control_is_unlearnable(1, 1008, 0, 648) is True
    with pytest.raises(SystemExit) as exc:
        p.GATE_ROUTE(**kwargs)
    assert all(marker in str(exc.value) for marker in p.COVERAGE_FLOOR_REFUSAL_MARKERS)

    kwargs["control_heldout_recall"] = 1 / 648
    assert p.control_is_unlearnable(1, 1008, 1, 648) is False
    try:
        p.GATE_ROUTE(**kwargs)
    except SystemExit as other:
        assert not any(m in str(other) for m in p.COVERAGE_FLOOR_REFUSAL_MARKERS), other

    assert p.control_is_unlearnable(0, 1008, 482, 648) is True
    for bad in ((1.0, 1008, 0, 648), (True, 1008, 0, 648), (5, 4, 0, 648), (0, 0, 0, 648)):
        with pytest.raises(SystemExit):
            p.control_is_unlearnable(*bad)


def test_v4_adv_n64_reading_re_reads_from_the_frontier(frontier):
    counts = frontier["verdicts"]["control_readings"]["adv_n64"]["recall_counts"]
    reading = phase29_prereg.V4_ADV_N64_READING
    assert reading["taught"] == tuple(counts["taught"])
    assert reading["heldout"] == tuple(counts["heldout"])


def test_refused_record_shape():
    p = phase29_prereg
    key = p.POINT_KEYS()[7]
    record = p.refused_record(key, taught=(1, 1008), heldout=(0, 648), recipe=_RECIPE)
    assert set(record) == set(p.REFUSED_RECORD_FIELDS)
    assert record["point_key"] == key
    assert record["control_key"] == p.control_key("n64") and key in p.leg_keys("n64")
    assert record["control_recall_counts"] == {"taught": [1, 1008], "heldout": [0, 648]}
    assert record["recipe"] == _RECIPE
    assert record["v4_adv_n64_reading"] is p.V4_ADV_N64_READING
    assert record["rule"] == "PREREG-03"


@pytest.mark.parametrize(
    "overrides",
    [
        {"heldout": (482, 648)},  # learnable control: nothing to refuse
        {"taught": (True, 1008)},  # a bool is not a count
        {"key": "adv_n64_ratio0p250000"},  # outside POINT_KEYS()
        {"recipe": {**_RECIPE, "lr": 1e-3}},  # an extra recipe key
        # WR-02: recipe VALUES against the key's leg
        {"recipe": {"replay_windows": 32, "n_facts": 8, "seed": 1337, "max_steps": 200}},
        {"recipe": {**_RECIPE, "replay_windows": 999}},
        {"recipe": {**_RECIPE, "n_facts": 8}},
        {"recipe": {**_RECIPE, "n_facts": 64.0}},
        {"recipe": {**_RECIPE, "seed": "x"}},
        {"recipe": {**_RECIPE, "seed": -1}},
        {"recipe": {**_RECIPE, "max_steps": -1}},
        {"recipe": {**_RECIPE, "max_steps": True}},
        {"key": phase29_prereg.POINT_KEYS()[1]},  # an n8 key under the n64 recipe
    ],
)
def test_refused_record_refuses(overrides):
    args = {
        "key": phase29_prereg.POINT_KEYS()[7],
        "taught": (1, 1008),
        "heldout": (0, 648),
        "recipe": _RECIPE,
        **overrides,
    }
    key = args.pop("key")
    with pytest.raises(SystemExit):
        phase29_prereg.refused_record(key, **args)


# =================================================================================================
# (6) AST GUARDS, EACH WATCHED RED ON A tmp_path COPY (D-04, D-05, D-19). The real file is only
#     ever read; the planted copy proves the guard can fire.
# =================================================================================================

_ACCOUNTANT_NAMES = {"epsilon_for", "sigma_for", "delta_closed", "delta_quadrature"}
_GATE_DEFS = {"mitigation_point_verdict", "corrected_point_verdict", "cleared_abc"}


def _module_targets(tree):
    """``(name, value)`` for every module-level Assign/AnnAssign target that is a Name."""
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    yield target.id, node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            yield node.target.id, node.value


def _numeric_constants(tree):
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float)
    ]


def _replay_literal_failures(source, value):
    tree = ast.parse(source)
    failures = [
        f"literal {n.value} at line {n.lineno}"
        for n in _numeric_constants(tree)
        if n.value == value
    ]
    failures += [
        f"assignment to {name}"
        for name, _ in _module_targets(tree)
        if name == "REPLAY_WINDOWS_PER_FACT"
    ]
    return failures


def _grid_retype_failures(source, grid):
    tree = ast.parse(source)
    failures = [
        f"re-typed grid at line {node.lineno}"
        for node in ast.walk(tree)
        if isinstance(node, (ast.Tuple, ast.List))
        and node.elts
        and all(isinstance(e, ast.Constant) for e in node.elts)
        and tuple(e.value for e in node.elts) == tuple(grid)
    ]
    failures += [
        f"grid endpoint literal at line {n.lineno}"
        for n in _numeric_constants(tree)
        if isinstance(n.value, float) and n.value == grid[-1]
    ]
    failures += [
        f"{name} not bound by reference"
        for name, value in _module_targets(tree)
        if name in ("ADVERSARIAL_RATIO_GRID", "RATIO_GRID")
        and not (isinstance(value, ast.Attribute) and value.attr == "ADVERSARIAL_RATIO_GRID")
    ]
    return failures


def _gate_retype_failures(source, f_y):
    tree = ast.parse(source)
    failures = [
        f"F_Y literal at line {n.lineno}"
        for n in _numeric_constants(tree)
        if isinstance(n.value, float) and n.value == f_y
    ]
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in _GATE_DEFS:
            failures.append(f"local def {node.name} at line {node.lineno}")
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            failures += [
                f"import of {alias.name} at line {node.lineno}"
                for alias in node.names
                if alias.name == "mitigation_point_verdict"
            ]
        elif isinstance(node, ast.Call):
            called = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if called == "mitigation_point_verdict":
                failures.append(f"call of {called} at line {node.lineno}")
    return failures


def _accountant_failures(source):
    failures = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.name for alias in node.names]
            if isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module)
            failures += [
                f"import {name} at line {node.lineno}"
                for name in names
                if name == "phase25_epsilon" or name.startswith("personacore.privacy")
            ]
        elif isinstance(node, ast.Name) and node.id in _ACCOUNTANT_NAMES:
            failures.append(f"name {node.id} at line {node.lineno}")
        elif isinstance(node, ast.Attribute) and node.attr in _ACCOUNTANT_NAMES:
            failures.append(f"attribute {node.attr} at line {node.lineno}")
    return failures


def _planted(tmp_path, source, planted, name):
    """Write the planted copy to tmp_path and read it back; prove the plant changed something."""
    assert planted != source, f"{name}: the plant did not change the source — vacuous"
    copied = tmp_path / name
    copied.write_text(planted, encoding="utf-8")
    return copied.read_text(encoding="utf-8")


def test_ast_replay_literal_guard(tmp_path):
    import teach_persona  # torch at import — inside the test only

    value = teach_persona.REPLAY_WINDOWS_PER_FACT
    real = _ROOT / PREREG
    source = real.read_text(encoding="utf-8")
    assert _replay_literal_failures(source, value) == []

    assigned = _planted(
        tmp_path, source, source + f"\nREPLAY_WINDOWS_PER_FACT = {value}\n", "assigned.py"
    )
    assert any("assignment" in f for f in _replay_literal_failures(assigned, value))
    literal = _planted(
        tmp_path, source, source + f"\n\ndef _w(n):\n    return n * {value}\n", "literal.py"
    )
    assert any("literal" in f for f in _replay_literal_failures(literal, value))
    assert real.read_text(encoding="utf-8") == source


def test_ast_grid_retype_guard(tmp_path):
    grid = mitigation_budget.ADVERSARIAL_RATIO_GRID
    real = _ROOT / PREREG
    source = real.read_text(encoding="utf-8")
    assert _grid_retype_failures(source, grid) == []

    anchor = "RATIO_GRID = mitigation_budget.ADVERSARIAL_RATIO_GRID"
    retyped = _planted(
        tmp_path, source, source.replace(anchor, f"RATIO_GRID = {grid!r}"), "grid.py"
    )
    failures = _grid_retype_failures(retyped, grid)
    assert any("re-typed grid" in f for f in failures), failures
    assert any("not bound by reference" in f for f in failures), failures
    assert real.read_text(encoding="utf-8") == source


def test_ast_gate_retype_guard(tmp_path):
    f_y = mitigation_gate.F_Y
    real = _ROOT / PREREG
    source = real.read_text(encoding="utf-8")
    assert _gate_retype_failures(source, f_y) == []

    local = _planted(
        tmp_path,
        source,
        source + "\n\ndef corrected_point_verdict(**kwargs):\n    return None\n",
        "local_def.py",
    )
    assert any("local def" in f for f in _gate_retype_failures(local, f_y))
    literal = _planted(
        tmp_path, source, source.replace("mitigation_gate.F_Y", repr(f_y), 1), "f_y.py"
    )
    assert any("F_Y literal" in f for f in _gate_retype_failures(literal, f_y))
    assert real.read_text(encoding="utf-8") == source


def test_no_v5_module_uses_the_accountant():
    modules = sorted(p for n in range(29, 35) for p in _SCRIPTS.glob(f"phase{n}_*.py"))
    assert modules, "no scripts/phase29_* .. phase34_* module found — the census is blind"
    for path in modules:
        assert _accountant_failures(path.read_text(encoding="utf-8")) == [], path
    # NON-VACUITY: the matcher fires where the accountant certainly is imported and called.
    epsilon = (_SCRIPTS / "phase25_epsilon.py").read_text(encoding="utf-8")
    assert _accountant_failures(epsilon)


def _strings(node):
    if isinstance(node, dict):
        for value in node.values():
            yield from _strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from _strings(value)
    elif isinstance(node, str):
        yield node


def test_named_limitations_record_p22_warning_4_5():
    entry = phase29_prereg.NAMED_LIMITATIONS["P22-WARNING-4/5"]
    assert set(entry) == {"reason", "source", "ledger_rows", "transitive_load"}
    assert "accountant" in entry["reason"] and "phase25_epsilon" in entry["transitive_load"]
    ledger = json.loads((_ROOT / "results" / "phase28_ledger.json").read_text(encoding="utf-8"))
    values = set(_strings(ledger))
    for row in entry["ledger_rows"]:
        assert row in values, row
    source_path = entry["source"].split(":", 1)[0]
    assert list(_ROOT.glob(source_path)), source_path
    assert "TD-16-R1" in values
    assert phase29_prereg.NAMED_LIMITATIONS["TD-16-R1-REPORT"]["ledger_rows"] == ("TD-16-R1",)


# =================================================================================================
# (8) THE ADMISSION CONTRACT, SCOPE RULE AND D-09 PINS (Plan 29-04, D-15 option 2). Every frontier
#     here is a forged 12-point dict; the 22 MB v4.0 frontier is never loaded.
# =================================================================================================

_CONTROL = {"taught": [40, 1008], "heldout": [20, 648]}
_MARKER_REASONS = ["(a) cleared", f"{mitigation_gate.REPLICATION_PENDING_MARKER} (GATE-08 / D-29)"]


def _forge(fr):
    """Re-derive verdicts.tallies and tallies_by_leg together from the entries."""
    p = phase29_prereg
    strings = [(k, p.point_verdict_string(fr["points"][k])) for k in fr["point_keys"]]

    def tally(values):
        values = list(values)
        return {name: values.count(name) for name in p._TALLY_NAMES}

    by_leg = {}
    for k, s in strings:
        by_leg.setdefault(k.rsplit("_", 1)[0], []).append(s)
    fr["verdicts"]["tallies"] = tally(s for _, s in strings)
    fr["verdicts"]["tallies_by_leg"] = {leg: tally(v) for leg, v in by_leg.items()}
    return fr


def _v5_frontier(verdicts_by_key=None, control_counts_by_leg=None, reasons_by_key=None):
    p = phase29_prereg
    verdicts_by_key = verdicts_by_key or {}
    reasons_by_key = reasons_by_key or {}
    counts = control_counts_by_leg or {leg: _CONTROL for leg in p.LEGS}
    points = {}
    for k in p.POINT_KEYS():
        v = verdicts_by_key.get(k, "FAIL")
        if v == p.REFUSED:
            entry = {"verdict": None, "early_return_reason": "own control unlearnable (PREREG-03)"}
        else:
            entry = {"verdict": v}
        entry["reasons"] = list(reasons_by_key.get(k, []))
        # The route kwargs a point graded against its leg's OWN advr control carries (CR-01).
        leg = next(leg for leg in p.LEGS if k in p.leg_keys(leg))
        rates = {side: kn[0] / kn[1] for side, kn in counts[leg].items()}
        prefixes = ("control", "point") if k == p.control_key(leg) else ("control",)
        for prefix in prefixes:
            for side, rate in rates.items():
                entry[f"{prefix}_{side}_recall"] = rate
        points[k] = {"verdict": entry}
    # Fresh lists per frontier: a mutating case must never leak into the shared _CONTROL.
    readings = {
        f"advr_{leg}": {"recall_counts": {s: list(v) for s, v in counts[leg].items()}}
        for leg in p.LEGS
    }
    return _forge(
        {
            "point_keys": list(p.POINT_KEYS()),
            "points": points,
            "verdicts": {"control_readings": readings},
        }
    )


def _keys(leg):
    return phase29_prereg.leg_keys(leg)


def test_admission_all_fail_is_moot():
    result = phase29_prereg.admission(_v5_frontier())
    assert result["verdict"] == "MOOT"
    assert result["admitted_point_keys"] == []
    assert not [r for r in result["reasons"] if "fully REFUSED" in r]


def test_admission_one_pass_is_admitted_regardless_of_promotion_fields():
    key = _keys("n64")[2]
    fr = _v5_frontier({key: "PASS"})
    fr["points"][key]["promotion_record"] = "anything"  # option 2 defines no promotion field
    result = phase29_prereg.admission(fr)
    assert result["verdict"] == "ADMITTED"
    assert result["admitted_point_keys"] == [key]
    assert result["control_readings"] == {leg: _CONTROL for leg in phase29_prereg.LEGS}


def test_admission_two_pass_in_key_order():
    later, earlier = _keys("n64")[1], _keys("n8")[-1]
    result = phase29_prereg.admission(_v5_frontier({later: "PASS", earlier: "PASS"}))
    assert result["verdict"] == "ADMITTED"
    assert result["admitted_point_keys"] == [earlier, later]


def test_admission_all_refused_does_not_raise():
    p = phase29_prereg
    counts = {"n8": {"taught": [0, 1008], "heldout": [0, 648]}, "n64": _CONTROL}
    fr = _v5_frontier({k: p.REFUSED for k in p.POINT_KEYS()}, counts)
    result = p.admission(fr)
    assert result["verdict"] == p.REFUSED
    joined = " ".join(result["reasons"])
    assert "could not be measured" in joined
    assert "advr_n8 control recall taught 0/1008, heldout 0/648" in joined
    assert "advr_n64 control recall taught 40/1008, heldout 20/648" in joined


def test_admission_mixed_refused_does_not_raise():
    p = phase29_prereg
    counts = {"n8": _CONTROL, "n64": {"taught": [1, 1008], "heldout": [0, 648]}}
    result = p.admission(_v5_frontier({k: p.REFUSED for k in _keys("n64")}, counts))
    assert result["verdict"] == "MOOT"
    refused = [r for r in result["reasons"] if "fully REFUSED" in r]
    assert len(refused) == 1
    assert "advr_n64" in refused[0] and "1/1008" in refused[0] and "0/648" in refused[0]
    assert "does not extend to that capacity" in refused[0]


def _drop_one(fr):
    key = fr["point_keys"].pop()
    del fr["points"][key]
    return fr


def _delete_entry(fr):
    del fr["points"][fr["point_keys"][3]]
    return fr


def _maybe(fr, with_pass):
    keys = fr["point_keys"]
    if with_pass:
        fr["points"][keys[1]]["verdict"]["verdict"] = "PASS"
    fr["points"][keys[2]]["verdict"]["verdict"] = "MAYBE"
    return _forge(fr)


def _tamper(fr):
    fr["points"][fr["point_keys"][1]]["verdict"]["verdict"] = "PASS"
    _forge(fr)
    fr["verdicts"]["tallies"]["PASS"] -= 1  # the entries say 1 PASS; the tally says 0
    return fr


def _tamper_by_leg(fr):
    fr["verdicts"]["tallies_by_leg"]["advr_n8"]["FAIL"] += 1
    return fr


def _bare_none(fr):
    fr["points"][fr["point_keys"][0]]["verdict"]["verdict"] = None
    return _forge(fr)


def _reasons_not_list(fr):
    fr["points"][fr["point_keys"][0]]["verdict"]["reasons"] = "text"
    return fr


def _no_control(fr):
    del fr["verdicts"]["control_readings"]["advr_n64"]
    return fr


def _bool_control(fr):
    fr["verdicts"]["control_readings"]["advr_n8"]["recall_counts"]["taught"] = [True, 1008]
    return fr


def _not_a_dict_point(fr):
    fr["points"][fr["point_keys"][0]] = "PASS"
    return fr


def _verdicts_not_dict(fr):
    fr["verdicts"] = ["x"]  # WR-01: raised AttributeError before
    return fr


def _verdicts_absent(fr):
    del fr["verdicts"]
    return fr


@pytest.mark.parametrize(
    "mutate",
    [
        _drop_one,
        _delete_entry,
        lambda fr: _maybe(fr, False),
        lambda fr: _maybe(fr, True),
        _tamper,
        _tamper_by_leg,
        _bare_none,
        _reasons_not_list,
        _no_control,
        _bool_control,
        _not_a_dict_point,
        _verdicts_not_dict,
        _verdicts_absent,
        lambda fr: None,
    ],
    ids=[
        "count-11",
        "entry-deleted",
        "maybe",
        "maybe-beats-pass",
        "tally-beats-pass",
        "by-leg-tally",
        "bare-none",
        "reasons-not-list",
        "control-missing",
        "bool-control-count",
        "point-not-dict",
        "verdicts-not-dict",
        "verdicts-absent",
        "absent",
    ],
)
def test_admission_inconclusive_takes_precedence(mutate):
    result = phase29_prereg.admission(mutate(_v5_frontier()))
    assert result["verdict"] == "INCONCLUSIVE", result
    assert result["admitted_point_keys"] == []


_UNLEARNABLE_N64 = {"n8": _CONTROL, "n64": {"taught": [1, 1008], "heldout": [0, 648]}}
_DP_N8 = {"taught": [790, 1008], "heldout": [346, 648]}  # v4.0 dp_n8 sigma=0 control counts


def _unlearnable_all_fail():
    return _v5_frontier(control_counts_by_leg=_UNLEARNABLE_N64)  # pre-fix: MOOT


def _unlearnable_one_pass():
    return _v5_frontier({_keys("n64")[2]: "PASS"}, _UNLEARNABLE_N64)  # pre-fix: ADMITTED


def _unlearnable_candidate():
    p = phase29_prereg
    key = _keys("n64")[2]
    verdicts = {k: p.REFUSED for k in _keys("n64")} | {key: "INCONCLUSIVE"}
    return _v5_frontier(verdicts, _UNLEARNABLE_N64, {key: _MARKER_REASONS})


def _pass_graded_against_dp():
    key = _keys("n8")[2]
    fr = _v5_frontier({key: "PASS"})
    fr["points"][key]["verdict"]["control_taught_recall"] = 790 / 1008  # pre-fix: ADMITTED
    return fr


def _readings_copied_from_dp():
    fr = _v5_frontier({_keys("n8")[1]: "PASS"})
    fr["verdicts"]["control_readings"]["advr_n8"]["recall_counts"] = {
        s: list(v) for s, v in _DP_N8.items()
    }
    return fr


def _pass_without_control_kwargs():
    key = _keys("n8")[1]
    fr = _v5_frontier({key: "PASS"})
    del fr["points"][key]["verdict"]["control_heldout_recall"]
    return fr


def _bool_control_kwarg():
    key = _keys("n64")[3]
    fr = _v5_frontier({key: "PASS"}, {"n8": _CONTROL, "n64": {"taught": [1, 1], "heldout": [1, 1]}})
    fr["points"][key]["verdict"]["control_taught_recall"] = True  # True == 1.0, but not a rate
    return fr


def _refused_record_cites_foreign_control():
    p = phase29_prereg
    fr = _v5_frontier({k: p.REFUSED for k in _keys("n64")}, _UNLEARNABLE_N64)
    fr["points"][_keys("n64")[1]]["verdict"]["control_recall_counts"] = dict(_DP_N8)
    return fr


@pytest.mark.parametrize(
    "build",
    [
        _unlearnable_all_fail,
        _unlearnable_one_pass,
        _unlearnable_candidate,
        _pass_graded_against_dp,
        _readings_copied_from_dp,
        _pass_without_control_kwargs,
        _bool_control_kwarg,
        _refused_record_cites_foreign_control,
    ],
)
def test_admission_reads_only_the_legs_own_control(build):
    """CR-01 (D-06, D-11, D-12, WR-05): an unlearnable or foreign control never admits, never
    reads CANDIDATE and never reads MOOT — the record contradicts its own counts: INCONCLUSIVE."""
    result = phase29_prereg.admission(build())
    assert result["verdict"] == "INCONCLUSIVE", result
    assert result["admitted_point_keys"] == []


def test_admission_learnable_leg_may_carry_route_refusals():
    """A learnable leg's REFUSED points (the route's ceiling / retention refusals) stay legal."""
    p = phase29_prereg
    fr = _v5_frontier({_keys("n64")[4]: p.REFUSED, _keys("n8")[1]: "PASS"})
    assert p.admission(fr)["admitted_point_keys"] == [_keys("n8")[1]]


def test_admission_candidate_unreplicated_is_never_moot():
    p = phase29_prereg
    key = _keys("n8")[2]
    fr = _v5_frontier({key: "INCONCLUSIVE"}, reasons_by_key={key: _MARKER_REASONS})
    result = p.admission(fr)
    assert result["verdict"] == p.CANDIDATE_UNREPLICATED
    assert key in result["reasons"][0]
    assert result["admitted_point_keys"] == []
    # A truncated-sweep INCONCLUSIVE (no marker) is not a candidate.
    truncated = _v5_frontier({key: "INCONCLUSIVE"}, reasons_by_key={key: ["curve truncated"]})
    assert p.admission(truncated)["verdict"] == "MOOT"
    # A stored PASS still wins over a candidate.
    other = _keys("n64")[1]
    both = _v5_frontier({key: "INCONCLUSIVE", other: "PASS"}, reasons_by_key={key: _MARKER_REASONS})
    assert p.admission(both)["admitted_point_keys"] == [other]


def test_threshold_reads_the_advr_control_and_refuses_dp():
    p = phase29_prereg
    counts = {"n8": {"taught": [30, 1008], "heldout": [9, 648]}, "n64": _CONTROL}
    fr = _v5_frontier(control_counts_by_leg=counts)
    assert p.recall_threshold(fr, "n8", "advr") == (p.F_Y * (30 / 1008), 30, 1008)
    for arm in ("dp", "adversarial", "adv"):
        with pytest.raises(SystemExit):
            p.recall_threshold(fr, "n8", arm)
    with pytest.raises(SystemExit):
        p.recall_threshold(fr, "n16", "advr")
    fr["verdicts"]["control_readings"]["advr_n8"]["recall_counts"]["taught"] = [True, 1008]
    with pytest.raises(SystemExit):
        p.recall_threshold(fr, "n8", "advr")


def test_scope_rule_covers_every_verdict():
    p = phase29_prereg
    assert set(p.SCOPE_RULE) == set(p.VERDICTS)
    key = _keys("n8")[1]
    admitted = p.admission(_v5_frontier({key: "PASS"}))
    assert p.relearning_scope(admitted)["relearn_point_keys"] == (key,)
    for verdict in p.VERDICTS:
        forged = {"verdict": verdict, "admitted_point_keys": [], "reasons": []}
        if verdict == "INCONCLUSIVE":
            with pytest.raises(SystemExit):
                p.relearning_scope(forged)
            continue
        scope = p.relearning_scope(forged)
        assert scope["rule"] == p.SCOPE_RULE[verdict]
        if verdict != "ADMITTED":
            assert scope["relearn_point_keys"] == ()
    assert "could not be measured" in p.SCOPE_RULE[p.REFUSED]
    assert "replication not pre-registered" in p.SCOPE_RULE[p.CANDIDATE_UNREPLICATED]
    with pytest.raises(SystemExit):
        p.relearning_scope({"verdict": "MAYBE", "admitted_point_keys": []})


def test_admission_schema_and_domains():
    p = phase29_prereg
    assert p.EXPECTED_POINTS == len(p.POINT_KEYS())
    assert p.VERDICTS == ("ADMITTED", "MOOT", "INCONCLUSIVE", "REFUSED", "CANDIDATE-UNREPLICATED")
    assert "points[<key>].verdict.reasons" in p.FRONTIER_SCHEMA
    assert "control_readings[<leg>]" in p.FRONTIER_SCHEMA
    assert "GATE-08-NO-PROMOTION" in p.NAMED_LIMITATIONS


_D09_PINS = (
    "MARGIN_K",
    "CURVE_K",
    "FULL_K",
    "RUNGS",
    "RELEARN_CAP",
    "MAX_STEPS",
    "CHECKPOINT_INTERVAL",
    "DESIGNATED_SEED",
    "FRESH_SEEDS",
    "POOLED_SEED_INDEX",
    "ATTACKER_CORPUS",
    "first_clear",
    "z_rule",
    "band",
    "recovery_gate",
    "promote_at_z",
    "point_verdict_string",
    "cleared_abc",
    "REFUSED",
)


def test_d09_pins_are_attribute_references():
    tree = ast.parse((_ROOT / PREREG).read_text(encoding="utf-8"))
    bound = list(_module_targets(tree))
    expected = {name: "phase27_prereg" for name in _D09_PINS} | {"V4_VERDICTS": "mitigation_gate"}
    for name, module in expected.items():
        values = [value for target, value in bound if target == name]
        assert len(values) == 1, (name, len(values))
        value = values[0]
        assert isinstance(value, ast.Attribute) and value.attr == name, name
        assert isinstance(value.value, ast.Name) and value.value.id == module, name
    # Secondary identity check, only where `is` is not vacuous (tuple / dict / function pins).
    p = phase29_prereg
    for name in ("RUNGS", "FRESH_SEEDS", "ATTACKER_CORPUS", "first_clear", "z_rule", "band"):
        assert getattr(p, name) is getattr(phase27_prereg, name), name
    for name in ("recovery_gate", "promote_at_z", "point_verdict_string", "cleared_abc"):
        assert getattr(p, name) is getattr(phase27_prereg, name), name
    assert p.V4_VERDICTS is mitigation_gate.V4_VERDICTS


def test_d09_never_taught_baselines_and_advr_control_source():
    p = phase29_prereg
    assert len(p.NEVER_TAUGHT_BASELINES) == len(phase27_prereg.FRESH_SEEDS)
    for name, value in p.NEVER_TAUGHT_BASELINES.items():
        assert name.startswith("never_taught_")
        assert value is phase27_prereg.PINNED_BASELINES[name]
    for leg in p.LEGS:
        assert p.control_baseline_source(leg) == (
            p.point_record_path(p.control_key(leg)) + "::adapter_sha256"
        )


def test_recovery_fixture_is_pinned_by_reference():
    import inspect

    import phase18_extraction  # torch at import — inside the test only
    import phase27_relearn  # git_sha() at import — inside the test only

    p = phase29_prereg
    module, attr = p.RECOVERY_FIXTURE_SOURCE[0].split(".")
    assert module == "phase27_relearn"
    assert getattr(phase27_relearn, attr) is phase27_relearn.disjointness_report
    assert phase18_extraction.CORPUS_SOURCE_FIXTURE == (
        phase18_extraction._REPO_ROOT / p.RECOVERY_FIXTURE_SOURCE[1]
    )
    reader = ast.parse(inspect.getsource(phase27_relearn.disjointness_report))
    assert any(
        isinstance(n, ast.Attribute) and n.attr == "CORPUS_SOURCE_FIXTURE" for n in ast.walk(reader)
    )
    _git("ls-files", "--error-unmatch", p.RECOVERY_FIXTURE_SOURCE[1])

    tree = ast.parse((_ROOT / PREREG).read_text(encoding="utf-8"))
    hits = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and n.value == p.RECOVERY_FIXTURE_SOURCE[1]
    ]
    assert len(hits) == 1
    readers = {"open", "read_text", "read_bytes", "load", "loads"}
    calls = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and (getattr(n.func, "id", None) or getattr(n.func, "attr", None)) in readers
    ]
    assert calls == []
