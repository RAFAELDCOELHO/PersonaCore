"""Plan 37-01: the Phase 37 pre-registration (REPRO-03 SC3/SC4), CPU-only.

What this file proves:
- the four rule functions behave as pre-registered on the committed Phase 19 records: replicated()
  (D-02/D-03), prefix_decision() (D-07), draw_identity() (D-03, description only) and
  nontarget_context() (D-12, context only);
- scripts/phase37_prereg.py is frozen before every results/phase37_* record (honest at zero
  records, natural RED on a file added before it), this file's FIRST add precedes every record's
  first add, and RECORDS_AT_COMMIT holds at the prereg's first commit's tree;
- the record and input paths resolve from the modules that own them; the D-02 tolerance and the
  D-06 cost are the records' arithmetic, never typed (literal scan, RED on a planted copy);
- every entry has exactly the four fields, none carries a proposer field, the preferences are
  exactly the labelled set, and one_attempt quotes D-11, D-15 and D-16 at their fixed commits;
- the module imports without torch, passes the v6.0 slot census, this file has zero skips, and
  every prereg function is called by a CPU test.

It reads only tracked files and git history and writes nothing under results/.
"""

import ast
import copy
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
import phase37_prereg  # noqa: E402  (same)

from test_phase29_prereg import _assert_frozen_before, _git, _planted  # noqa: E402
from test_phase35_prereg import (  # noqa: E402
    _insert_at,
    _literal_failures,
    _slot_census_failures,
)
from test_phase36_prereg import (  # noqa: E402
    _HEAVY,
    _entries_node,
    _entry_string_failures,
    _first_inner,
    _skip_failures,
    _untested_functions,
)

PREREG = "scripts/phase37_prereg.py"


def _record(rel):
    return json.loads((_ROOT / rel).read_text(encoding="utf-8"))


def _committed_assertions():
    return dict(phase35_prereg.R1A_ASSERTIONS)


def _committed_prefix():
    return _record("results/phase19_collateral_curve.json")["ordered_prefix"]


def _committed_draws():
    return _record("results/phase19_arm_erased.json")["draws"]


# =================================================================================================
# (1) replicated() (D-02, D-03).
# =================================================================================================


def test_replicated_on_the_committed_assertions():
    out = phase37_prereg.replicated(_committed_assertions())
    assert out["verdict"] == "REPLICATED"
    assert set(out["per_key"]) == set(phase35_prereg.R1A_ASSERTIONS)
    for key, row in out["per_key"].items():
        assert row["abs_diff"] == 0, key
        assert row["within"] is True, key
    # A JSON round trip turns the tuples into lists; they are accepted.
    assert json.loads(json.dumps(out))["verdict"] == "REPLICATED"
    listed = json.loads(json.dumps(_committed_assertions()))
    assert isinstance(listed["target_correct"], list)
    assert phase37_prereg.replicated(listed)["verdict"] == "REPLICATED"


def test_replicated_destroyed_pct_tolerance_is_inclusive():
    committed = phase35_prereg.R1A_ASSERTIONS["destroyed_pct"]
    edge = committed + phase37_prereg.DESTROYED_PCT_TOLERANCE
    assert phase37_prereg.replicated({**_committed_assertions(), "destroyed_pct": edge})[
        "verdict"
    ] == ("REPLICATED")
    beyond = math.nextafter(edge, math.inf)
    out = phase37_prereg.replicated({**_committed_assertions(), "destroyed_pct": beyond})
    assert out["verdict"] == "NOT_REPLICATED"
    assert out["per_key"]["destroyed_pct"]["within"] is False


@pytest.mark.parametrize(
    "key,value",
    [("k", 79), ("target_correct", (1, 27)), ("target_correct", (0, 26))],
)
def test_replicated_zero_tolerances_and_equal_denominators(key, value):
    out = phase37_prereg.replicated({**_committed_assertions(), key: value})
    assert out["verdict"] == "NOT_REPLICATED"
    assert out["per_key"][key]["within"] is False


def test_replicated_unequal_denominator_with_zero_numerator_diff():
    out = phase37_prereg.replicated({**_committed_assertions(), "target_correct": (0, 26)})
    assert out["per_key"]["target_correct"]["abs_diff"] == 0
    assert out["per_key"]["target_correct"]["within"] is False


def test_replicated_refuses_a_missing_key():
    partial = {k: v for k, v in _committed_assertions().items() if k != "k"}
    with pytest.raises(SystemExit, match=r"^\[phase37_prereg\]"):
        phase37_prereg.replicated(partial)


# =================================================================================================
# (2) prefix_decision() (D-07).
# =================================================================================================


def test_prefix_decision_identical_prefix_runs_the_arm():
    committed = _committed_prefix()
    k = phase35_prereg.R1A_ASSERTIONS["k"]
    out = phase37_prereg.prefix_decision(k, committed, committed)
    assert out["run_arm"] is True
    assert out["k_equal"] is True and out["set_equal"] is True
    assert out["positions_moved"] == 0
    assert out["only_in_remeasured"] == [] and out["only_in_committed"] == []
    json.dumps(out)


def test_prefix_decision_reordered_set_runs_the_arm_and_counts_moves():
    committed = _committed_prefix()
    reordered = list(reversed(committed))
    k = phase35_prereg.R1A_ASSERTIONS["k"]
    out = phase37_prereg.prefix_decision(k, reordered, committed)
    assert out["run_arm"] is True
    expected = sum(a != b for a, b in zip(reordered, committed, strict=True))
    assert expected > 0
    assert out["positions_moved"] == expected


def test_prefix_decision_k_other_than_committed_does_not_run():
    committed = _committed_prefix()
    k = phase35_prereg.R1A_ASSERTIONS["k"] + 1
    out = phase37_prereg.prefix_decision(k, committed, committed)
    assert out["run_arm"] is False
    assert out["k_equal"] is False
    assert out["positions_moved"] is None


def test_prefix_decision_one_address_replaced_does_not_run():
    committed = _committed_prefix()
    replaced = copy.deepcopy(committed)
    replaced[0] = [99, "fc_in", 99]
    k = phase35_prereg.R1A_ASSERTIONS["k"]
    out = phase37_prereg.prefix_decision(k, replaced, committed)
    assert out["run_arm"] is False
    assert out["set_equal"] is False
    assert out["only_in_remeasured"] == [[99, "fc_in", 99]]
    assert out["only_in_committed"] == [list(committed[0])]


def test_prefix_decision_refuses_a_committed_list_of_the_wrong_length():
    committed = _committed_prefix()
    k = phase35_prereg.R1A_ASSERTIONS["k"]
    with pytest.raises(SystemExit, match=r"^\[phase37_prereg\]"):
        phase37_prereg.prefix_decision(k, committed, committed[:-1])


# =================================================================================================
# (3) draw_identity() (D-03: description, never a criterion).
# =================================================================================================


def test_draw_identity_on_the_committed_draws():
    draws = _committed_draws()
    out = phase37_prereg.draw_identity(draws, draws)
    assert out["bit_identical"] is True
    assert out["differing_completions"] == 0 and out["differing_entries"] == 0
    assert out["n_completions"] == sum(len(d["completions"]) for d in draws)
    assert out["n_completions"] == len(draws) * len(draws[0]["completions"])
    assert out["n_entries"] == len(draws)
    assert out["criterion"] is False


def test_draw_identity_counts_one_changed_completion():
    draws = _committed_draws()
    replica = copy.deepcopy(draws)
    replica[5]["completions"][3] = replica[5]["completions"][3] + "!"
    out = phase37_prereg.draw_identity(replica, draws)
    assert out["bit_identical"] is False
    assert out["differing_completions"] == 1
    assert out["differing_entries"] == 1


def test_draw_identity_counts_a_short_replica_without_raising():
    draws = _committed_draws()
    out = phase37_prereg.draw_identity(draws[:-1], draws)
    assert out["bit_identical"] is False
    assert out["differing_entries"] == 1
    assert out["differing_completions"] == len(draws[-1]["completions"])


# =================================================================================================
# (4) nontarget_context() (D-12: context, never a criterion).
# =================================================================================================


def _nontarget_deltas():
    floor = _record("results/phase19_noise_floors.json")["nontarget_noise_floor"]
    return floor, dict(zip(floor["slot_order"], floor["deltas_in_slot_order"], strict=True))


def test_nontarget_context_per_slot():
    floor, committed = _nontarget_deltas()
    replica = {slot: delta + 0.25 for slot, delta in committed.items()}
    out = phase37_prereg.nontarget_context(replica, committed)
    assert out["criterion"] is False
    assert out["noise_floor"] == floor["value"]
    assert set(out["slots"]) == set(committed)
    for slot, row in out["slots"].items():
        assert row["replica_delta"] == replica[slot]
        assert row["committed_delta"] == committed[slot]
        assert row["abs_diff"] == abs(replica[slot] - committed[slot])
        assert row["noise_floor"] == floor["value"]
    json.dumps(out)


def test_nontarget_context_refuses_mismatched_slots():
    _, committed = _nontarget_deltas()
    replica = dict(committed)
    replica.pop(next(iter(replica)))
    with pytest.raises(SystemExit, match=r"^\[phase37_prereg\]"):
        phase37_prereg.nontarget_context(replica, committed)


def test_rule_inputs_must_be_finite_numbers():
    phase37_prereg._prove_number("ok", 1.5)
    for bad in (True, math.nan, math.inf, "1"):
        with pytest.raises(SystemExit, match=r"^\[phase37_prereg\]"):
            phase37_prereg._prove_number("x", bad)
    with pytest.raises(SystemExit, match=r"^\[phase37_prereg\]"):
        phase37_prereg.replicated({**_committed_assertions(), "k": True})


# =================================================================================================
# (5) ANCESTRY (REPRO-03 SC4, T-37-01).
# =================================================================================================


def _strictly_before(x, y):
    run = subprocess.run(("git", "merge-base", "--is-ancestor", x, y), cwd=_ROOT, check=False)
    return x != y and run.returncode == 0


def _first_add(path):
    return _git("log", "--diff-filter=A", "--format=%H", "--", path).split()[-1]


def _phase37_records():
    return sorted(_git("ls-files", "results/phase37_*").split())


def test_phase37_prereg_is_frozen_before_every_phase37_record():
    _assert_frozen_before(PREREG, _phase37_records())
    # NON-VACUITY (natural RED): the v6.0 pre-registration was added before this one existed.
    with pytest.raises(subprocess.CalledProcessError):
        _assert_frozen_before(PREREG, ["scripts/phase35_prereg.py"])


def test_this_test_file_is_first_added_before_every_phase37_record():
    # Only the FIRST add: a later fix to this file must not redden the guard forever.
    mine = _first_add("tests/test_phase37_prereg.py")
    for record in _phase37_records():
        assert _strictly_before(mine, _first_add(record)), record
    # NON-VACUITY: the same check against a file added long before this one is False.
    assert not _strictly_before(mine, _first_add("scripts/phase35_prereg.py"))


def test_records_at_commit_is_true_at_the_first_commit():
    first = _git("log", "--format=%H", "--", PREREG).split()[-1]
    at_first = _git("ls-tree", "-r", "--name-only", first, "--", "results/").split()
    assert at_first, "meta-guard: the first commit's results/ tree is empty, the check is vacuous"
    assert not [p for p in at_first if p.startswith("results/phase37_")]
    assert phase37_prereg.RECORDS_AT_COMMIT == 0


# =================================================================================================
# (6) PATHS RESOLVE FROM THE MODULES THAT OWN THEM (D-01, D-05).
# =================================================================================================


def test_record_paths_and_inputs_resolve_from_the_modules():
    import phase19_erasure as pin  # torch at import: inside the test only
    import phase19_run

    assert phase37_prereg.RECORDS == (
        "results/phase37_r1a.json",
        "results/phase37_r1b_arm.json",
        "results/phase37_r1b.json",
    )
    assert phase37_prereg.RECORD_GLOB in phase35_prereg.V6_RESULT_PATHS
    for path in phase37_prereg.RECORDS:
        assert fnmatch.fnmatch(path, phase37_prereg.RECORD_GLOB), path
    assert (
        phase37_prereg.ERASED_RECORD
        == pin.arm_record_path("erased").resolve().relative_to(_ROOT).as_posix()
    )
    assert (
        phase37_prereg.CURVE_RECORD
        == phase19_run.TARGET_CURVE_PATH.resolve().relative_to(_ROOT).as_posix()
    )
    assert phase37_prereg.BUDGET_RECORD == "results/phase36_budget.json"

    # W2: r1b_scope partitions the pin's pre-erasure block; the keys come from the pin.
    scope = phase37_prereg.ENTRIES["r1b_scope"]["value"]
    measured = {
        n.removeprefix("pre_erasure.") for n in scope["re_measured"] if n.startswith("pre_erasure.")
    }
    assert measured == set(pin.PRE_ERASURE_KEYS) - {"per_fact"}
    assert "pre_erasure.per_fact" in scope["inherited"]
    assert "pre_erasure.per_fact" not in scope["re_measured"]


# =================================================================================================
# (7) D-02 AND D-06: THE RECORDS' ARITHMETIC (T-37-02, T-37-03, T-37-06).
# =================================================================================================


def test_d02_tolerance_is_the_records_arithmetic_in_d02_order():
    floor = _record("results/phase19_noise_floors.json")["dialogue_ppl_noise_floor"]["value"]
    pre = _record("results/phase19_arm_erased.json")["pre_erasure"]["dialogue_ppl"]
    g0 = pre["adapter_on"] - pre["adapter_off"]
    expected = phase35_prereg.MARGIN_K * floor / g0 * 100
    tolerance = phase37_prereg.DESTROYED_PCT_TOLERANCE
    assert expected == tolerance
    assert phase37_prereg.destroyed_pct_tolerance(floor, g0) == tolerance
    filled = phase37_prereg.R1B_TOLERANCE_AND_REPLICATED
    assert filled["tolerance"]["destroyed_pct"] == tolerance
    # The order is part of the pre-registration: x 100 first lands one ulp away.
    assert 100 * phase35_prereg.MARGIN_K * floor / g0 != tolerance

    assert set(filled["tolerance"]) == set(phase35_prereg.R1A_ASSERTIONS)
    for key in ("k", "target_correct", "nontargets_beyond_margin"):
        value = filled["tolerance"][key]
        assert type(value) is int and value == 0, key
        assert phase37_prereg.ENTRIES[f"tolerance_{key}"]["kind"] == "preference", key
    definition = filled["replicated_definition"]
    entry = phase37_prereg.ENTRIES["replicated_definition"]
    assert set(definition) == set(entry)
    for field in entry:
        assert definition[field] == entry[field], field

    arm = _record("results/phase19_arm_erased.json")["config"]["wall_clock_min"]
    sweep = _record("results/phase19_collateral_curve.json")["wall_clock_min"]
    assert phase37_prereg.r1b_cost_hours(arm, sweep) == (arm + sweep) / 60
    assert phase37_prereg.R1B_COST_HOURS == (arm + sweep) / 60
    front = _record("results/phase36_budget.json")["front_hours"]["R1b"]
    cap = phase36_prereg.ENTRIES["front_stop_factor"]["value"] * front
    assert phase37_prereg.R1B_COST_CAP_HOURS == cap
    assert phase37_prereg.R1B_COST_HOURS <= cap


def _forbidden_floats():
    floats = {
        phase37_prereg.DESTROYED_PCT_TOLERANCE,
        phase37_prereg.R1B_COST_HOURS,
        phase37_prereg.R1B_COST_CAP_HOURS,
        phase37_prereg.DIALOGUE_FLOOR,
        phase37_prereg.NONTARGET_FLOOR,
        phase37_prereg.G0,
    }
    assert all(type(f) is float for f in floats), "meta-guard: a census value is not a float"
    return floats


def test_no_derived_value_is_typed_in_the_prereg(tmp_path):
    real = _ROOT / PREREG
    before = real.read_bytes()
    source = before.decode("utf-8")
    floats = _forbidden_floats()
    assert _literal_failures(source, set(), floats, set()) == []
    planted = source + f"\nX = {phase37_prereg.DESTROYED_PCT_TOLERANCE!r}\n"
    assert _literal_failures(_planted(tmp_path, source, planted, "typed.py"), set(), floats, set())
    assert real.read_bytes() == before


# =================================================================================================
# (8) ENTRIES: EXACTLY FOUR FIELDS, NO PROPOSER, HONEST KINDS (PREREG-06/07, T-37-04).
# =================================================================================================


def _good_entry():
    return {"value": 1, "derivation": "d", "kind": "derived", "source": "s"}


def test_entries_have_exactly_four_fields_and_no_proposer(tmp_path):
    assert phase37_prereg.ENTRY_FIELDS is phase35_prereg.ENTRY_FIELDS
    assert phase37_prereg.KINDS is phase35_prereg.KINDS
    for name, entry in phase37_prereg.ENTRIES.items():
        assert set(entry) == {"value", "derivation", "kind", "source"}, name
        assert "proposer" not in entry and "adopted_by" not in entry, name
    with pytest.raises(TypeError):
        phase37_prereg.ENTRIES["planted"] = {}
    assert phase37_prereg._prove_entries() is None

    phase37_prereg._prove_entry("ok", _good_entry())
    refused = (
        {**_good_entry(), "proposer": "Rafael"},
        {**_good_entry(), "adopted_by": "Rafael"},
        {k: v for k, v in _good_entry().items() if k != "source"},
        {**_good_entry(), "kind": "guess"},
        {**_good_entry(), "derivation": ""},
        {**_good_entry(), "value": phase37_prereg.FORBIDDEN_PHRASE},
        [1],
    )
    for entry in refused:
        with pytest.raises(SystemExit, match=r"^\[phase37_prereg\]"):
            phase37_prereg._prove_entry("x", entry)

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
        source, first.lineno, first.col_offset + 1, phase37_prereg.FORBIDDEN_PHRASE
    )
    ast.parse(planted_phrase)
    assert _entry_string_failures(_planted(tmp_path, source, planted_phrase, "phrase.py"))
    assert real.read_bytes() == before


def test_prove_and_read():
    with pytest.raises(SystemExit, match=r"^\[phase37_prereg\] x$"):
        phase37_prereg._prove(False, "x")
    assert phase37_prereg._prove(True, "x") is None
    read = phase37_prereg._read(phase37_prereg.ERASED_RECORD)
    assert isinstance(read, dict) and "pre_erasure" in read


_CONTEXT_PATH = ".planning/phases/37-clean-reproduction-of-the-phase-19-verdict/37-CONTEXT.md"


def _ruling(commit, decision):
    """One addendum bullet at a fixed commit, markdown removed, whitespace collapsed."""
    text = _git("show", f"{commit}:{_CONTEXT_PATH}")
    addendum = text.split("<addendum>", 1)[1].split("</addendum>", 1)[0]
    lines = addendum.splitlines()
    head = f"- **{decision}:** "
    start = next(i for i, line in enumerate(lines) if line.startswith(head))
    bullet = [lines[start].removeprefix(head)]
    for line in lines[start + 1 :]:
        if not line.startswith("  "):
            break
        bullet.append(line)
    flat = " ".join(bullet).replace("**", "").replace("`", "")
    return " ".join(flat.split())


def test_one_attempt_quotes_rulings():
    derivation = " ".join(phase37_prereg.ENTRIES["one_attempt"]["derivation"].split())
    source = phase37_prereg.ENTRIES["one_attempt"]["source"]
    for commit, decision in (("d710181", "D-11"), ("1eec113", "D-15"), ("1eec113", "D-16")):
        quote = _ruling(commit, decision)
        assert len(quote.split()) > 15, f"meta-guard: {decision} bullet parsed too short"
        assert quote in derivation, decision
        assert re.search(rf"{decision} \({commit}\)", source), decision
    # NON-VACUITY: a ruling that is not quoted is not found.
    assert _ruling("d710181", "D-12") not in derivation


def test_preferences_are_labelled():
    kinds = {name: entry["kind"] for name, entry in phase37_prereg.ENTRIES.items()}
    derived = {"tolerance_destroyed_pct", "r1b_cost_hours"}
    assert {n for n, k in kinds.items() if k == "derived"} == derived
    assert {n for n, k in kinds.items() if k == "preference"} == set(kinds) - derived
    assert len(kinds) == len(set(kinds)) and len(kinds) > len(derived)


# =================================================================================================
# (9) CPU-ONLY AT IMPORT, THE SLOT CENSUS, ZERO SKIPS, EVERY FUNCTION CALLED (T-37-05).
# =================================================================================================


def test_the_prereg_imports_without_torch():
    probe = (
        "import sys; sys.path.insert(0, 'scripts'); import phase37_prereg; "
        f"print(*[name in sys.modules for name in {_HEAVY!r}])"
    )
    out = subprocess.run(
        [sys.executable, "-c", probe], cwd=_ROOT, capture_output=True, text=True, check=True
    )
    assert out.stdout.split() == ["False"] * len(_HEAVY), out.stdout


def test_phase37_scripts_pass_the_slot_census():
    paths = sorted(_SCRIPTS.glob("phase37_*.py"))
    assert paths, "meta-guard: no scripts/phase37_*.py, the census would be vacuous"
    sources = [(p.relative_to(_ROOT).as_posix(), p.read_text(encoding="utf-8")) for p in paths]
    assert _slot_census_failures(sources) == []


def test_no_skips_in_this_file(tmp_path):
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert _skip_failures(source) == []
    planted = source + '\n\ndef test_planted():\n    pytest.skip("x")\n'
    assert _skip_failures(_planted(tmp_path, source, planted, "skip.py"))


def test_every_phase37_prereg_function_has_a_cpu_test(tmp_path):
    real = _ROOT / PREREG
    before = real.read_bytes()
    source = before.decode("utf-8")
    test_source = pathlib.Path(__file__).read_text(encoding="utf-8")
    defs = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)]
    assert defs, "meta-guard: the prereg defines no function, the census would be vacuous"
    assert _untested_functions("phase37_prereg", source, test_source) == []

    planted = source + '\n\ndef planted_untested():\n    """Planted."""\n'
    copied = _planted(tmp_path, source, planted, "untested.py")
    assert _untested_functions("phase37_prereg", copied, test_source) == ["planted_untested"]
    assert real.read_bytes() == before
