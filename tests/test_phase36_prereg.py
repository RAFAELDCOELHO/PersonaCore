"""Plan 36-01: the Phase 36 pre-registration (D-17, D-19, Q5), CPU-only.

What this file proves:
- scripts/phase36_prereg.py is frozen before every results/phase36_* file (honest at zero records,
  natural RED on a file added before it), and RECORDS_AT_COMMIT holds at its FIRST commit's tree;
- every entry has exactly the four fields, none carries a proposer field (runtime + AST, RED on
  planted copies), and the preferences are exactly the labelled set;
- P22 (RECIPE-04) holds at the step cap and refuses a T whose onset reaches the noised grid;
- every divergence comparator and every record-priced stage resolves on a committed record;
- the cut order follows D-15 literally; the probe records are isolated; the module imports without
  torch; scripts/phase36_*.py pass the v6.0 slot census; zero skips; every function has a CPU test.

It reads only tracked files and git history and writes nothing under results/.
"""

import ast
import fnmatch
import json
import math
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
_TESTS = str(_ROOT / "tests")
if _TESTS not in sys.path:
    sys.path.insert(0, _TESTS)

import phase35_prereg  # noqa: E402  (scripts/ is not a package)
import phase36_prereg  # noqa: E402  (same)

from test_phase29_prereg import _assert_frozen_before, _git, _planted  # noqa: E402
from test_phase35_prereg import _insert_at, _slot_census_failures  # noqa: E402

PREREG = "scripts/phase36_prereg.py"


# =================================================================================================
# (1) ANCESTRY (COST-01 SC4, T-36-01).
# =================================================================================================


def test_phase36_prereg_is_frozen_before_every_phase36_record():
    tracked = sorted(_git("ls-files", "results/phase36_*").split())
    _assert_frozen_before(PREREG, tracked)
    # NON-VACUITY (natural RED): the v6.0 pre-registration was added before this one existed.
    with pytest.raises(subprocess.CalledProcessError):
        _assert_frozen_before(PREREG, ["scripts/phase35_prereg.py"])


def test_records_at_commit_is_true_at_the_first_commit():
    first = _git("log", "--format=%H", "--", PREREG).split()[-1]
    at_first = _git("ls-tree", "-r", "--name-only", first, "--", "results/").split()
    assert at_first, "meta-guard: the first commit's results/ tree is empty, the check is vacuous"
    assert not [p for p in at_first if p.startswith("results/phase36_")]
    assert phase36_prereg.RECORDS_AT_COMMIT == 0


# =================================================================================================
# (2) ENTRIES: EXACTLY FOUR FIELDS, NO PROPOSER (D-17, PREREG-07, T-36-03).
# =================================================================================================


def test_entries_have_exactly_the_four_fields():
    entries = phase36_prereg.ENTRIES
    assert len(entries) == 17
    assert phase36_prereg.ENTRY_FIELDS is phase35_prereg.ENTRY_FIELDS
    assert phase36_prereg.KINDS is phase35_prereg.KINDS
    for name, entry in entries.items():
        assert set(entry) == {"value", "derivation", "kind", "source"}, name
        assert entry["kind"] in ("derived", "preference"), name
        assert isinstance(entry["derivation"], str) and entry["derivation"].strip(), name
        assert isinstance(entry["source"], str) and entry["source"].strip(), name
    with pytest.raises(TypeError):
        entries["planted"] = {}
    assert phase36_prereg._prove_entries() is None


def _good_entry():
    return {"value": 1, "derivation": "d", "kind": "derived", "source": "s"}


def test_entries_refuse_an_unknown_kind_or_missing_field():
    phase36_prereg._prove_entry("ok", _good_entry())
    bad_kind = {**_good_entry(), "kind": "guess"}
    missing_source = {k: v for k, v in _good_entry().items() if k != "source"}
    empty_derivation = {**_good_entry(), "derivation": ""}
    phrase = {**_good_entry(), "value": phase36_prereg.FORBIDDEN_PHRASE}
    for entry in (bad_kind, missing_source, empty_derivation, phrase, [1]):
        with pytest.raises(SystemExit, match=r"^\[phase36_prereg\]"):
            phase36_prereg._prove_entry("x", entry)


_PROVENANCE_KEYS = ("proposer", "adopted_by")


def _entries_node(tree):
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "_ENTRIES" for target in node.targets
        ):
            return node
    return None


def _entry_string_failures(source):
    tree = ast.parse(source)
    failures = []
    entries = _entries_node(tree)
    if entries is None:
        return ["no module-level _ENTRIES assignment"]
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key in node.keys:
                if isinstance(key, ast.Constant) and key.value in _PROVENANCE_KEYS:
                    failures.append(f"dict key {key.value!r} at line {key.lineno}")
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and phase36_prereg.FORBIDDEN_PHRASE in node.value
        ):
            failures.append(f"forbidden phrase at line {node.lineno}")
    return failures


def _first_inner(entries, wanted_key):
    """(key node, value node) of the first inner-dict item keyed `wanted_key`, in source order."""
    found = []
    for node in ast.walk(entries.value):
        if isinstance(node, ast.Dict) and node is not entries.value:
            for key, value in zip(node.keys, node.values, strict=True):
                if isinstance(key, ast.Constant) and key.value == wanted_key:
                    found.append((key, value))
    assert found, f"no inner {wanted_key!r} key in _ENTRIES"
    return min(found, key=lambda pair: (pair[0].lineno, pair[0].col_offset))


def test_no_proposer_or_adopted_by_in_any_entry(tmp_path):
    for name, entry in phase36_prereg.ENTRIES.items():
        for banned in _PROVENANCE_KEYS:
            assert banned not in entry, name
    for banned in _PROVENANCE_KEYS:
        with pytest.raises(SystemExit) as refused:
            phase36_prereg._prove_entry("x", {**_good_entry(), banned: "Rafael"})
        assert banned in str(refused.value)

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
        source, first.lineno, first.col_offset + 1, phase36_prereg.FORBIDDEN_PHRASE
    )
    ast.parse(planted_phrase)
    assert _entry_string_failures(_planted(tmp_path, source, planted_phrase, "phrase.py"))

    assert real.read_bytes() == before


def test_preferences_are_labelled():
    preferences = {n for n, e in phase36_prereg.ENTRIES.items() if e["kind"] == "preference"}
    assert preferences == {
        "divergence_tolerance",
        "e3_max_steps",
        "e4_reserve_points",
        "e4_first_point_check",
        "high_bound_rule",
        "front_stop_factor",
        "stop_line_factor",
        "projection_rule",
        "cut_table_min_seeds",
        "e2_proposed_seed_count",
        "cut_order",
    }


# =================================================================================================
# (3) P22 AT THE STEP CAP, AND THE SEED ENTRIES (D-05, D-14).
# =================================================================================================


def test_p22_holds_at_the_step_cap():
    cap = phase36_prereg.ENTRIES["e3_max_steps"]["value"]
    assert cap == 4 * phase35_prereg.STEP_BUDGET
    assert phase36_prereg.ENTRIES["e3_probe_steps"]["value"] == (phase35_prereg.STEP_BUDGET, cap)
    smallest = min(s for s in phase35_prereg.E3_SIGMAS if s > 0)
    assert phase36_prereg.prove_p22(cap) < smallest
    # RED: at T = 20000 the onset (~0.789) reaches the noised grid.
    assert phase35_prereg.p22_onset_sigma(20000) >= smallest
    with pytest.raises(SystemExit, match="RECIPE-04"):
        phase36_prereg.prove_p22(20000)


def test_seed_entries_fit_the_seed_list():
    least = phase36_prereg.ENTRIES["cut_table_min_seeds"]["value"]
    proposed = phase36_prereg.ENTRIES["e2_proposed_seed_count"]["value"]
    assert least <= proposed <= len(phase35_prereg.seed_list())
    assert least >= phase35_prereg.ENTRIES["e2_min_seeds"]["value"]


# =================================================================================================
# (4) DIVERGENCE: COMPARATORS RESOLVE ON COMMITTED RECORDS, THE FORMULA (D-02, D-04, T-36-04).
# =================================================================================================


def _resolve(node, key_path):
    """The values at `key_path` in `node`; a "*" segment maps over a list."""
    if not key_path:
        return [node]
    head, rest = key_path[0], key_path[1:]
    if head == "*":
        assert isinstance(node, list) and node, f"'*' over {type(node).__name__}"
        return [v for item in node for v in _resolve(item, rest)]
    return _resolve(node[head], rest)


def _tracked(path):
    return _git("ls-files", "--error-unmatch", path) == path


def _assert_positive_numbers(path, key_path):
    assert _tracked(path), path
    values = _resolve(json.loads((_ROOT / path).read_text(encoding="utf-8")), key_path)
    assert values, (path, key_path)
    for value in values:
        assert isinstance(value, (int, float)) and not isinstance(value, bool), (path, value)
        assert math.isfinite(value) and value > 0, (path, value)


def test_comparators_resolve_on_committed_records_for_divergence():
    rows = phase36_prereg.ENTRIES["divergence_comparators"]["value"]
    ids = [row["id"] for row in rows]
    assert len(ids) == len(set(ids))
    for row in rows:
        path, key = row["historical_path"], row["historical_key"]
        if path is None:
            assert key is None, row["id"]
            continue
        if isinstance(key, str):  # a regex over a markdown report
            assert _tracked(path), path
            found = re.findall(key, (_ROOT / path).read_text(encoding="utf-8"))
            assert found == ["2.1"], found
            assert float(found[0]) == 2.1
        else:
            _assert_positive_numbers(path, key)
    assert phase36_prereg.E3_PROBE_POINT_RECORD == "results/phase25_point_dp_n8_sigma0p500000.json"
    assert {r["id"] for r in rows if r["gated"]} == {
        "r1b_e1_k48",
        "e2_a2_pass",
        "e3_t200_train",
        "e3_t200_score",
        "e3_t800_linearity",
        "e5_clearance",
    }
    unprobed = [r for r in rows if r["probe_field"] is None]
    assert [r["id"] for r in unprobed] == ["e1_phase31_beside"]
    assert unprobed[0]["gated"] is False
    r1b = next(r for r in rows if r["id"] == "r1b_e1_k48")
    assert r1b["historical_path"] == "results/phase19_arm_erased.json"
    assert r1b["historical_key"] == ("config", "wall_clock_min")

    # The record-priced stages (D-19, Q5) resolve too.
    _assert_positive_numbers(*phase36_prereg.ENTRIES["e4_canary_scoring_price"]["value"])
    _assert_positive_numbers(*phase36_prereg.ENTRIES["e1_ordering_price"]["value"])
    for path, key in phase36_prereg.ENTRIES["e1_calibration_price"]["value"].values():
        _assert_positive_numbers(path, key)

    row = phase36_prereg._row("i", "E1", None, None, None, "s", False)
    assert dict(row) == {
        "id": "i",
        "front": "E1",
        "probe_field": None,
        "historical_path": None,
        "historical_key": None,
        "unit": "s",
        "gated": False,
    }
    with pytest.raises(TypeError):
        row["id"] = "x"


def test_divergence_formula():
    assert phase36_prereg.divergence(125, 100) == 0.25
    assert phase36_prereg.exceeds(125, 100) is False
    assert phase36_prereg.exceeds(125.0001, 100) is True
    assert phase36_prereg.exceeds(75, 100) is False
    for args in ((1, 0), (1, -1), (math.nan, 1), (1, math.inf), (True, 1)):
        with pytest.raises(SystemExit):
            phase36_prereg.divergence(*args)
    with pytest.raises(SystemExit, match=r"^\[phase36_prereg\] x$"):
        phase36_prereg._prove(False, "x")


# =================================================================================================
# (5) THE CUT ORDER (D-14, D-15) AND THE HIGH-BOUND RULES (W5/W6).
# =================================================================================================


def test_cut_order_follows_d15():
    order = phase36_prereg.ENTRIES["cut_order"]["value"]
    assert isinstance(order, tuple) and len(order) == len(set(order))
    assert order[:5] == (
        "e4_reserve",
        "e6_anchor_adapters",
        "e2_seeds_to_3",
        "e3_whole",
        "e1_checkpoints",
    )
    assert order[5:] == ("r1b", "e1_core")
    assert "e2_seeds_to_3" in order
    assert [row for row in order if "seeds" in row] == ["e2_seeds_to_3"]
    assert phase36_prereg.ENTRIES["cut_table_min_seeds"]["value"] == 3


def test_high_bound_rule_lists_ruling_alternatives():
    rule = phase36_prereg.ENTRIES["high_bound_rule"]["value"]
    assert set(rule) == {"H1", "H2", "H3", "ruling_alternatives"}
    alternatives = rule["ruling_alternatives"]
    assert set(alternatives) == {"a2_draw_basis", "single_run_draw_loop", "e1_calibration"}
    for pair in alternatives.values():
        assert isinstance(pair, tuple) and len(pair) == 2
        assert all(isinstance(item, str) and item for item in pair)
        assert pair[0] != pair[1]
    assert [alternatives[k][0] for k in ("a2_draw_basis", "single_run_draw_loop")] == [
        "k78",
        "within_run",
    ]
    assert alternatives["e1_calibration"][0] == "records"


# =================================================================================================
# (6) PROBE RECORD ISOLATION (D-16).
# =================================================================================================


def test_probe_records_are_isolated():
    others = [p for p in phase35_prereg.V6_RESULT_PATHS if p != phase36_prereg.PROBE_GLOB]
    assert phase36_prereg.PROBE_GLOB in phase35_prereg.V6_RESULT_PATHS
    assert len(phase36_prereg.PROBE_RECORDS) == len(phase36_prereg.PROBE_FRONTS)
    for front, path in zip(phase36_prereg.PROBE_FRONTS, phase36_prereg.PROBE_RECORDS, strict=True):
        assert phase36_prereg.probe_record(front) == path
        assert fnmatch.fnmatch(path, phase36_prereg.PROBE_GLOB)
        assert not any(fnmatch.fnmatch(path, pattern) for pattern in others), path
        assert path != "results/phase36_budget.json"
    with pytest.raises(SystemExit):
        phase36_prereg.probe_record("e4")


# =================================================================================================
# (7) CPU-ONLY AT IMPORT, THE SLOT CENSUS, ZERO SKIPS.
# =================================================================================================

_HEAVY = ("torch", "teach_persona", "phase19_erasure", "phase18_extraction", "phase23_run")


def test_the_prereg_imports_without_torch():
    probe = (
        "import sys; sys.path.insert(0, 'scripts'); import phase36_prereg; "
        f"print(*[name in sys.modules for name in {_HEAVY!r}])"
    )
    out = subprocess.run(
        [sys.executable, "-c", probe], cwd=_ROOT, capture_output=True, text=True, check=True
    )
    assert out.stdout.split() == ["False"] * len(_HEAVY), out.stdout


def test_phase36_scripts_pass_the_slot_census():
    paths = sorted(_SCRIPTS.glob("phase36_*.py"))
    assert paths, "meta-guard: no scripts/phase36_*.py, the census would be vacuous"
    sources = [(p.relative_to(_ROOT).as_posix(), p.read_text(encoding="utf-8")) for p in paths]
    assert _slot_census_failures(sources) == []


_SKIP_ATTRS = ("skip", "skipif", "importorskip", "xfail")


def _skip_failures(source):
    failures = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Attribute) and node.attr in _SKIP_ATTRS:
            failures.append(f"{node.attr} at line {node.lineno}")
        elif isinstance(node, ast.Name) and node.id == "_MPS_SKIP":
            failures.append(f"_MPS_SKIP at line {node.lineno}")
    return failures


def test_no_skips_in_this_file(tmp_path):
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert _skip_failures(source) == []
    planted = source + '\n\ndef test_planted():\n    pytest.skip("x")\n'
    assert _skip_failures(_planted(tmp_path, source, planted, "skip.py"))


# =================================================================================================
# (8) EVERY FUNCTION HAS A CPU TEST. Later Phase 36 test files import this helper.
# =================================================================================================


def _untested_functions(module_name, module_source, test_source):
    """Module-level defs of `module_name` that `test_source` never CALLS, either as
    ``<module_name>.<def>(...)`` or as a bare call of a name imported ``from <module_name>``. A bare
    mention (e.g. an ``is`` assert) is not a test."""
    tree = ast.parse(test_source)
    imported = {
        alias.asname or alias.name
        for n in ast.walk(tree)
        if isinstance(n, ast.ImportFrom) and n.module == module_name
        for alias in n.names
    }
    calls = [n.func for n in ast.walk(tree) if isinstance(n, ast.Call)]
    named = {f.id for f in calls if isinstance(f, ast.Name) and f.id in imported}
    named |= {
        f.attr
        for f in calls
        if isinstance(f, ast.Attribute)
        and isinstance(f.value, ast.Name)
        and f.value.id == module_name
    }
    defs = [n.name for n in ast.parse(module_source).body if isinstance(n, ast.FunctionDef)]
    return sorted(name for name in defs if name not in named)


def test_every_phase36_prereg_function_has_a_cpu_test(tmp_path):
    real = _ROOT / PREREG
    before = real.read_bytes()
    source = before.decode("utf-8")
    test_source = pathlib.Path(__file__).read_text(encoding="utf-8")
    defs = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)]
    assert defs, "meta-guard: the prereg defines no function, the census would be vacuous"
    assert _untested_functions("phase36_prereg", source, test_source) == []

    planted = source + '\n\ndef planted_untested():\n    """Planted."""\n'
    copied = _planted(tmp_path, source, planted, "untested.py")
    assert _untested_functions("phase36_prereg", copied, test_source) == ["planted_untested"]

    # A bare mention is not a test; only a call is.
    mentioned = test_source + "\nassert phase36_prereg.planted_untested is not None\n"
    assert _untested_functions("phase36_prereg", copied, mentioned) == ["planted_untested"]
    called = test_source + "\nphase36_prereg.planted_untested()\n"
    assert _untested_functions("phase36_prereg", copied, called) == []
    other = test_source + "\nother.planted_untested()\n"  # a call on another module
    assert _untested_functions("phase36_prereg", copied, other) == ["planted_untested"]
    imported = test_source + "\nfrom phase36_prereg import planted_untested\nplanted_untested()\n"
    assert _untested_functions("phase36_prereg", copied, imported) == []

    assert real.read_bytes() == before
