"""Plan 41-02: the Phase 41 pre-registration, fill file 1 (ERASE-04, ERASE-07 fills; ERASE-03, -05,
-06, -09, -10 written as entries), CPU-only.

What this file proves:
- the record paths are read from the Phase 35 registry, ORDERINGS is ("greedy", the filled
  alternative ordering), and the three fills that must precede every results/phase41_* record
  (e1_checkpoint_grid, e1_alternative_ordering, e1_condition_b_margin) are the registry's objects;
- the caps check runs at import with the grid's count only, never a K = 48 confirmation count.
- plan 41-03: the gate composition (per-target (a)/(b)/(c), the cell verdict, pair labels, summary
  counts, the fill-input builders) and the declared descriptive readings, on committed records.

It reads only tracked files and git history and writes nothing under results/.
"""

import ast
import collections.abc
import fnmatch
import inspect
import json
import os
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
import phase36_caps  # noqa: E402  (same)
import phase41_prereg  # noqa: E402  (same)

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
        phase41_prereg.calibration_record("greedy", 1337)
        == "results/phase41_calibration_greedy_seed1337.json"
    )
    assert (
        phase41_prereg.band_record(2024, "gradient")
        == "results/phase41_band_inputs_gradient_seed2024.json"
    )
    assert (
        phase41_prereg.cell_record("cat_name", "greedy", 1337)
        == "results/phase41_cell_cat_name_greedy_seed1337.json"
    )
    assert (
        phase41_prereg.k16_record("pet_name", "gradient", 2024, 48)
        == "results/phase41_k16_pet_name_gradient_seed2024_k048.json"
    )
    assert (
        phase41_prereg.k48_record("street", "greedy", 1337, 128)
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


# =================================================================================================
# (2) THE ENTRIES: EVERY DECISION WRITTEN BEFORE ANY RECORD (Task 2).
# =================================================================================================

_D01_D25 = "447747c"
_D26_D28 = "3787b9d"
_LOG = ".planning/phases/41-erasure-across-facts-orderings-and-seeds/41-DISCUSSION-LOG.md"
_D26_PREFIX = '> "Opção 2, com duas amarras:'

_DECISION_ENTRIES = frozenset(
    {
        "e1_checkpoint_grid",
        "e1_alternative_ordering",
        "targets",
        "seeds_and_adapters",
        "stop_rule",
        "k48_confirmations",
        "calibration",
        "condition_a",
        "condition_b",
        "condition_c",
        "verdict",
        "pair_labels",
        "summary_line",
        "m1_m2",
        "varies_label",
        "d13_block",
        "predictions",
        "d06_correlation",
        "d12_side_by_side",
        "execution_order",
        "e1_pause",
        "crash_rule",
        "operations",
        "e1_share_hours",
        "e1_unit_prices",
    }
)

_LABEL = "default taken at plan time, not yet confirmed by Rafael"
# Keyed by ENTRY NAME: the decision id its derivation cites. Plan 41-05 removes each name once
# Rafael confirms or changes that default.
_UNCONFIRMED = {
    "record_layout": "D-22",
    "alternative_variant": "D-05",
    "not_run": "D-17",
    "resume_declaration": "D-23",
    "d02_equality": "D-02",
    "control_gap_scope": "D-13",
    "approvals": "ERASE-06",
    "prep_order": "D-10",
    "stop_for_rafael": "D-24",
}


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
    entries = phase41_prereg.ENTRIES
    assert set(entries) == _DECISION_ENTRIES | set(_UNCONFIRMED)
    assert len(entries) == len(_DECISION_ENTRIES) + len(_UNCONFIRMED)
    for name, entry in entries.items():
        assert re.search(r"\b(D-\d\d|ERASE-\d\d)\b", entry["derivation"]), name
        assert _D01_D25 in entry["source"] or _D26_D28 in entry["source"], name
        expected = "derived" if name in ("e1_share_hours", "e1_unit_prices") else "preference"
        assert entry["kind"] == expected, name
        assert _no_mutable_containers(entry["value"]), name
    budget = _record(phase41_prereg.BUDGET_RECORD)
    assert entries["e1_share_hours"]["value"] == budget["front_hours"]["E1"]
    prices = entries["e1_unit_prices"]["value"]
    assert set(prices) == {
        "e1_calibration_seconds",
        "e1_k16_seconds",
        "e1_k48_seconds",
        "e1_ordering_seconds",
    }
    for key, price in prices.items():
        assert price == budget["unit_prices"][key], key
    assert "D-07" in entries["e1_checkpoint_grid"]["derivation"]
    assert "D-26" in entries["k48_confirmations"]["derivation"]
    assert _D26_D28 in entries["k48_confirmations"]["source"]


def _d26_quote(log_text):
    lines = [line for line in log_text.splitlines() if line.startswith(_D26_PREFIX)]
    assert len(lines) == 1, "meta-guard: the D-26 reply is not exactly one line"
    (line,) = lines
    return line[line.index('"') + 1 : line.rindex('"')]


def test_d26_ruling_is_quoted_verbatim():
    quote = _d26_quote(_git("show", f"{_D26_D28}:{_LOG}"))
    assert phase41_prereg.D26_RULING == quote
    assert quote in phase41_prereg.ENTRIES["k48_confirmations"]["derivation"]
    # NON-VACUITY: one character changed fails the same equality.
    changed = quote[:-1] + ("!" if quote[-1] != "!" else "?")
    assert changed != quote and changed != phase41_prereg.D26_RULING


def test_k48_deviation_is_declared():
    entry = phase41_prereg.ENTRIES["k48_confirmations"]
    value = entry["value"]
    budget = _record(phase41_prereg.BUDGET_RECORD)
    assert value["max_per_cell"] == len(phase41_prereg.GRID)
    assert value["per_checkpoint"] == 1
    assert value["committed_cap"] == budget["unit_caps"]["E1"]["k48_confirms_per_cell"]
    for phrase in ("deviation", "pricing assumption", "no pause per confirmation"):
        assert phrase in entry["derivation"], phrase
    # The committed cap is not what binds: passing the count would be refused.
    with pytest.raises(SystemExit, match="k48_confirms_per_cell"):
        phase36_caps.check_unit_caps("E1", k48_confirms_per_cell=value["max_per_cell"])


def test_predictions_are_recorded_before_any_run():
    predictions = phase41_prereg.ENTRIES["predictions"]["value"]
    assert set(predictions) == {
        "d11_calibration_identity",
        "d21_d13_at_stop",
        "greedy_1337_phase19_prefix",
        "d02_cpu_equality",
    }
    for name, text in predictions.items():
        assert "descriptive" in text, name
        assert "a mismatch is a finding, not a failure" in text, name
    d11 = predictions["d11_calibration_identity"]
    for phrase in (
        "phase19_erasure.CALIBRATION_ARM",
        "phase19_erasure.RETRAIN_PREFIX",
        "teach_persona.arm_outputs",
        "torch.equal",
        phase41_prereg.D11_REFERENCE_RECORD,
        phase41_prereg.D11_REFERENCE_KEY,
        phase41_prereg.D11_REFERENCE_SHA256,
    ):
        assert phrase in d11, phrase
    assert (
        phase41_prereg.D11_REFERENCE_SHA256 in phase41_prereg.ENTRIES["predictions"]["derivation"]
    )


def test_d11_reference_digest_is_read_from_the_committed_record():
    import phase19_erasure
    import phase19_run
    import teach_persona

    p = phase41_prereg
    _git("ls-files", "--error-unmatch", p.D11_REFERENCE_RECORD)  # tracked, never the .pt
    assert _ROOT / p.D11_REFERENCE_RECORD == phase19_run.CURVE_PATH
    record = _record(p.D11_REFERENCE_RECORD)
    assert p.D11_REFERENCE_SHA256 == record[p.D11_REFERENCE_KEY]
    assert re.fullmatch(r"[0-9a-f]{64}", p.D11_REFERENCE_SHA256)
    # The record's input adapter is the arm the prediction compares against (by file name: the
    # record's absolute path is host-specific).
    adapter = teach_persona.arm_outputs(
        phase19_erasure.CALIBRATION_ARM, prefix=phase19_erasure.RETRAIN_PREFIX
    )["adapter"]
    assert pathlib.Path(record["adapter_in"]).name == pathlib.Path(adapter).name


def test_value_nll_bound_is_the_budget_price_over_the_components():
    import phase19_erasure

    price = _record(phase41_prereg.BUDGET_RECORD)["unit_prices"]["e1_ordering_seconds"]
    assert phase41_prereg.value_nll_seconds() == price / phase19_erasure.N_COMPONENTS
    assert phase41_prereg.VALUE_NLL_SECONDS == phase41_prereg.value_nll_seconds()
    assert phase41_prereg.MAX_GRADIENTS_PER_CELL == len(phase41_prereg.GRID)
    assert phase41_prereg.GRADIENT_HEADROOM == price / (
        len(phase41_prereg.GRID) * phase41_prereg.VALUE_NLL_SECONDS
    )
    derivation = phase41_prereg.ENTRIES["e1_alternative_ordering"]["derivation"]
    assert repr(phase41_prereg.VALUE_NLL_SECONDS) in derivation
    assert repr(phase41_prereg.GRADIENT_HEADROOM) in derivation


def test_defaults_are_labelled():
    assert phase41_prereg._DEFAULT == _LABEL
    for name, entry in phase41_prereg.ENTRIES.items():
        if name in _UNCONFIRMED:
            assert _LABEL in entry["derivation"], name
            assert _UNCONFIRMED[name] in entry["derivation"], name
        else:
            assert _LABEL not in entry["derivation"], name


# =================================================================================================
# (3) ANCESTRY (SC5, T-41-04): frozen before every results/phase41_* record. Honest at zero records
# and after them. Plan 41-12's floors test imports _strictly_before and _first_add from here.
# =================================================================================================


def _strictly_before(x, y):
    run = subprocess.run(("git", "merge-base", "--is-ancestor", x, y), cwd=_ROOT, check=False)
    return x != y and run.returncode == 0


def _first_add(path):
    return _git("log", "--diff-filter=A", "--format=%H", "--", path).split()[-1]


def _phase41_records():
    return sorted(_git("ls-files", "results/phase41_*").split())


def test_phase41_prereg_is_frozen_before_every_phase41_record():
    _assert_frozen_before(PREREG, _phase41_records())
    # NON-VACUITY (natural RED): the v6.0 pre-registration was added before this one existed.
    with pytest.raises(subprocess.CalledProcessError):
        _assert_frozen_before(PREREG, ["scripts/phase35_prereg.py"])


def test_this_test_file_is_first_added_before_every_phase41_record():
    # Only the FIRST add: a later fix to this file must not redden the guard forever.
    mine = _first_add("tests/test_phase41_prereg.py")
    for record in _phase41_records():
        assert _strictly_before(mine, _first_add(record)), record
    # NON-VACUITY: the same check against a file added long before this one is False.
    assert not _strictly_before(mine, _first_add("scripts/phase35_prereg.py"))


def test_records_at_commit_is_true_at_the_first_commit():
    first = _git("log", "--format=%H", "--", PREREG).split()[-1]
    at_first = _git("ls-tree", "-r", "--name-only", first, "--", "results/").split()
    assert at_first, "meta-guard: the first commit's results/ tree is empty, the check is vacuous"
    assert not [path for path in at_first if path.startswith("results/phase41_")]
    assert phase41_prereg.RECORDS_AT_COMMIT == 0


# =================================================================================================
# (4) NOTHING DERIVED IS TYPED (T-41-05): the GRID node is the one exemption (D-07).
# =================================================================================================


def _grid_node(tree):
    (node,) = [
        n
        for n in tree.body
        if isinstance(n, ast.Assign)
        and len(n.targets) == 1
        and isinstance(n.targets[0], ast.Name)
        and n.targets[0].id == "GRID"
    ]
    return node


def _without_grid(source):
    """``source`` with the GRID assignment's value replaced by ``None`` (same line count)."""
    node = _grid_node(ast.parse(source))
    lines = source.splitlines(keepends=True)
    blank = ["\n"] * (node.end_lineno - node.lineno)
    lines[node.lineno - 1 : node.end_lineno] = [" " * node.col_offset + "GRID = None\n", *blank]
    return "".join(lines)


def _k_literals_outside_grid(source):
    """Every int constant equal to CURVE_K or FULL_FIDELITY_K that lies outside the GRID node."""
    tree = ast.parse(source)
    grid = _grid_node(tree)
    inside = {id(n) for n in ast.walk(grid)}
    ks = {phase35_prereg.CURVE_K, phase35_prereg.FULL_FIDELITY_K}
    return [
        n.lineno
        for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and type(n.value) is int and n.value in ks
        if id(n) not in inside
    ]


def _census_sets():
    import phase19_erasure as pin

    p = phase41_prereg
    noise = _record(p.NOISE_FLOOR_RECORD)
    budget = _record(p.BUDGET_RECORD)
    retention = _record("results/phase20_retention_floor.json")
    floor = noise["gap_noise_floor"]
    gaps = [noise["per_seed"][str(s)]["full"]["dialogue_gap"]["gap"] for s in p.SEEDS]
    bands = [
        edge
        for gap in gaps
        for edge in phase35_prereg.DIALOGUE_GAP_BAND(control_gap=gap, gap_noise_floor=floor)
    ]
    seeds = {
        phase35_prereg.CURVE_K,
        phase35_prereg.FULL_FIDELITY_K,
        pin.N_TARGET_QUESTIONS,
        pin.N_COMPONENTS,
        *phase35_prereg.e1_teaching_seeds(),
        len(p.TARGETS) * len(p.ORDERINGS) * len(p.SEEDS),
        len(p.TARGETS) * len(p.ORDERINGS),
    }
    floats = {
        p.E1_CONDITION_B_MARGIN,
        floor,
        *gaps,
        *bands,
        budget["front_hours"]["E1"],
        *(budget["unit_prices"][k] for k in p.ENTRIES["e1_unit_prices"]["value"]),
        retention["cap"],
        retention["retention_ppl_noise_floor"],
        p.VALUE_NLL_SECONDS,
        p.GRADIENT_HEADROOM,
    }
    assert len(bands) == 2 * len(gaps) and len(gaps) == len(p.SEEDS), "meta-guard: bands"
    assert all(type(f) is float for f in floats), "meta-guard: a census value is not a float"
    assert all(type(i) is int for i in seeds), "meta-guard: a census value is not an int"
    return seeds, floats


def test_no_derived_value_is_typed_in_the_prereg(tmp_path):
    seeds, floats = _census_sets()
    real = _ROOT / PREREG
    before = real.read_bytes()
    source = before.decode("utf-8")
    # The GRID literal holds 16 and 48 by design (D-07); without it nothing derived is typed.
    assert _literal_failures(source, seeds, floats, set()), "meta-guard: GRID is not scanned"
    scanned = _without_grid(source)
    assert scanned.count("\n") == source.count("\n")
    assert _literal_failures(scanned, seeds, floats, set()) == []
    assert _k_literals_outside_grid(source) == []
    plants = [
        ("k48.py", f"\nX = {phase35_prereg.FULL_FIDELITY_K!r}\n"),
        ("margin.py", f"\nX = {phase41_prereg.E1_CONDITION_B_MARGIN!r}\n"),
        ("hours.py", f"\nX = {phase41_prereg.ENTRIES['e1_share_hours']['value']!r}\n"),
    ]
    for name, line in plants:
        planted = _planted(tmp_path, source, source + line, name)
        assert _literal_failures(_without_grid(planted), seeds, floats, set()), name
    planted = _planted(tmp_path, source, source + plants[0][1], "k48_outside.py")
    assert _k_literals_outside_grid(planted)
    assert real.read_bytes() == before


# =================================================================================================
# (5) ENTRIES: EXACTLY FOUR FIELDS, NO PROPOSER; THE PRIVATE HELPERS.
# =================================================================================================


def _good_entry():
    return {"value": 1, "derivation": "d", "kind": "derived", "source": "s"}


def test_entries_have_exactly_four_fields_and_no_proposer(tmp_path):
    assert phase41_prereg.ENTRY_FIELDS is phase35_prereg.ENTRY_FIELDS
    assert phase41_prereg.KINDS is phase35_prereg.KINDS
    assert phase41_prereg.FORBIDDEN_PHRASE is phase35_prereg.FORBIDDEN_PHRASE
    for name, entry in phase41_prereg.ENTRIES.items():
        assert set(entry) == {"value", "derivation", "kind", "source"}, name
    assert phase41_prereg._prove_entries() is None

    phase41_prereg._prove_entry("ok", _good_entry())
    refused = (
        {**_good_entry(), "proposer": "Rafael"},
        {**_good_entry(), "adopted_by": "Rafael"},
        {k: v for k, v in _good_entry().items() if k != "source"},
        {**_good_entry(), "kind": "guess"},
        {**_good_entry(), "derivation": ""},
        {**_good_entry(), "value": phase41_prereg.FORBIDDEN_PHRASE},
        [1],
    )
    for entry in refused:
        with pytest.raises(SystemExit, match=r"^\[phase41_prereg\]"):
            phase41_prereg._prove_entry("x", entry)

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
        source, first.lineno, first.col_offset + 1, phase41_prereg.FORBIDDEN_PHRASE
    )
    ast.parse(planted_phrase)
    assert _entry_string_failures(_planted(tmp_path, source, planted_phrase, "phrase.py"))
    assert real.read_bytes() == before


def test_prove_count_read_and_path_helpers():
    with pytest.raises(SystemExit, match=r"^\[phase41_prereg\] x$"):
        phase41_prereg._prove(False, "x")
    assert phase41_prereg._prove(True, "x") is None
    assert phase41_prereg._prove_count("n", 0) is None
    for bad in (True, -1, 1.0):
        with pytest.raises(SystemExit, match=r"^\[phase41_prereg\]"):
            phase41_prereg._prove_count("n", bad)
    read = phase41_prereg._read(phase41_prereg.BUDGET_RECORD)
    assert isinstance(read, dict) and "unit_caps" in read

    glob = phase41_prereg.RECORD_GLOB
    calibration = phase41_prereg.calibration_record(*phase41_prereg.ORDERINGS[:1], 1337)
    assert phase41_prereg._prove_path(calibration, glob) == calibration
    with pytest.raises(SystemExit, match="prep record"):
        phase41_prereg._prove_path(calibration, glob, unit=True)
    with pytest.raises(SystemExit, match="does not match"):
        phase41_prereg._prove_path("results/phase40_x.json", glob)
    assert phase41_prereg._prove_unit() is None
    assert phase41_prereg._prove_unit(seed=2024, checkpoint=phase41_prereg.GRID[-1]) is None
    with pytest.raises(SystemExit, match="checkpoint"):
        phase41_prereg._prove_unit(checkpoint=phase41_prereg.GRID[-1] + 1)


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
import phase41_prereg

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
    "grid": list(phase41_prereg.E1_CHECKPOINT_GRID["checkpoints"]),
    "planted": [os.fspath(p) for p in planted],
    "planted_flagged": list(_FLAGGED),
}}))
"""


def test_importing_the_prereg_opens_no_checkpoint(tmp_path):
    """This file loads torch through e1_teaching_seeds() by design; an "open" audit hook watches
    the import. Blind spot: safetensors opens files in Rust without a Python "open" audit event,
    so a safetensors read is invisible to the hook; the sys.modules leg covers it."""
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
    assert tuple(result["grid"]) == phase41_prereg.GRID
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


def _phase41_script_sources():
    paths = sorted(_SCRIPTS.glob("phase41_*.py"))
    sources = [(p.relative_to(_ROOT).as_posix(), p.read_text(encoding="utf-8")) for p in paths]
    assert PREREG in {rel for rel, _ in sources}, "meta-guard: the census would miss the prereg"
    return sources


def test_phase41_scripts_pass_the_slot_census():
    assert _slot_census_failures(_phase41_script_sources()) == []
    assert fnmatch.fnmatch(PREREG, phase35_prereg.owner_prereg_glob("e1_checkpoint_grid"))


def test_no_skips_in_this_file(tmp_path):
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert _skip_failures(source) == []
    planted = source + '\n\ndef test_planted():\n    pytest.skip("x")\n'
    assert _skip_failures(_planted(tmp_path, source, planted, "skip.py"))


def test_census_every_phase41_prereg_function_has_a_cpu_test(tmp_path):
    real = _ROOT / PREREG
    before = real.read_bytes()
    source = before.decode("utf-8")
    test_source = pathlib.Path(__file__).read_text(encoding="utf-8")
    defs = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)]
    assert defs, "meta-guard: the prereg defines no function, the census would be vacuous"
    assert _untested_functions("phase41_prereg", source, test_source) == []

    planted = source + '\n\ndef planted_untested():\n    """Planted."""\n'
    copied = _planted(tmp_path, source, planted, "untested.py")
    assert _untested_functions("phase41_prereg", copied, test_source) == ["planted_untested"]
    assert real.read_bytes() == before


# =================================================================================================
# (7) D-26 AND ERASE-03 GATES OVER EVERY scripts/phase41_*.py (the driver and the floors file join
# when they exist). Plan 41-10's driver test imports _typed_target_failures.
# =================================================================================================


def _k48_caps_call_failures(source):
    """Every check_unit_caps call carrying a k48_confirms_per_cell keyword (D-26)."""
    return [
        f"check_unit_caps(k48_confirms_per_cell=...) at line {node.lineno}"
        for node in _caps_calls(source)
        if any(k.arg == "k48_confirms_per_cell" for k in node.keywords)
    ]


def test_no_check_unit_caps_with_k48_confirms_in_phase41_scripts(tmp_path):
    for rel, source in _phase41_script_sources():
        assert _k48_caps_call_failures(source) == [], rel
    source = _prereg_source()
    plant = '\nphase36_caps.check_unit_caps("E1", k48_confirms_per_cell=2)\n'
    planted = _planted(tmp_path, source, source + plant, "k48_call.py")
    assert _k48_caps_call_failures(planted)


def _typed_target_failures(source):
    """Every non-docstring str constant EQUAL to a member of phase35_prereg.e1_targets() (a typed
    target name). Containment inside longer prose is allowed."""
    tree = ast.parse(source)
    docstrings = _docstring_nodes(tree)
    targets = set(phase35_prereg.e1_targets())
    assert targets, "meta-guard: no targets, the scan would be vacuous"
    return [
        f"typed target {n.value!r} at line {n.lineno}"
        for n in ast.walk(tree)
        if isinstance(n, ast.Constant)
        and isinstance(n.value, str)
        and id(n) not in docstrings
        and n.value in targets
    ]


def test_no_target_name_is_typed_in_phase41_scripts(tmp_path):
    for rel, source in _phase41_script_sources():
        assert _typed_target_failures(source) == [], rel
    source = _prereg_source()
    target = phase35_prereg.e1_targets()[-2]
    planted = _planted(tmp_path, source, source + f"\nX = {target!r}\n", "typed.py")
    assert _typed_target_failures(planted)
    documented = source + f'\n\ndef planted():\n    """Names {target}."""\n'
    assert _typed_target_failures(_planted(tmp_path, source, documented, "doc.py")) == []
    prose = source + f"\nX = {('erase ' + target)!r}\n"
    assert _typed_target_failures(_planted(tmp_path, source, prose, "prose.py")) == []


# =================================================================================================
# (8) THE GATE COMPOSITION (plan 41-03 Task 1, D-15 / D-16 / D-17 / D-09, ERASE-06 / -09 / -10):
# rows, the K = read_k count, conditions (a)/(b)/(c), the cell verdict, the pair labels, the summary
# counts, the NOT_REACHED sentence and the two fill-input builders, on real committed records.
# =================================================================================================

_K064 = "results/erasure_kstar_arm_k064.json"
_VERDICT_DOMAIN = ("SUCCESS", "FAILURE", "INCONCLUSIVE", "NOT_REACHED", "NOT_RUN")


def _phase40_a2(group, seed):
    import phase40_prereg

    return _record(phase40_prereg.a2_record(group, seed))


def _truncated(draws, k):
    """The first ``k`` completions of every draw (and ``stopped`` alike): a K = k read of the same
    draws."""
    return [{**d, "completions": d["completions"][:k], "stopped": d["stopped"][:k]} for d in draws]


def test_nontarget_slots():
    import phase18_extraction

    core = phase18_extraction.CORE_SLOTS
    for target in phase41_prereg.TARGETS:
        slots = phase41_prereg.nontarget_slots(target)
        assert len(slots) == 7 == len(core) - 1
        assert target not in slots
        assert set(slots) | {target} == set(core)
        assert slots == tuple(s for s in core if s != target)
    with pytest.raises(SystemExit, match=r"^\[phase41_prereg\]"):
        phase41_prereg.nontarget_slots("hometown")


def test_record_rows_on_real_records():
    import phase18_extraction

    post = phase41_prereg.record_rows(_record(_K064))
    assert post["pet_name"]["n_answerable"] == 0
    assert post["pet_name"]["n_questions"] == 27
    assert set(post) == set(phase18_extraction.CORE_SLOTS)
    pre = phase41_prereg.record_rows(_phase40_a2("full", 1337))
    assert pre["pet_name"]["n_answerable"] == 27
    # Only K = confirm_k records: a2_rows proves the Phase 18 k.
    off_k = _record(_K064)
    off_k["config"]["k"] = phase41_prereg.E1_CHECKPOINT_GRID["read_k"]
    with pytest.raises(SystemExit, match="Phase 18"):
        phase41_prereg.record_rows(off_k)


def test_k16_target_count_is_the_prefix_of_the_k48_draws():
    import phase18_extraction

    record = _record(_K064)
    read_k = phase41_prereg.E1_CHECKPOINT_GRID["read_k"]
    draws = _truncated(record["draws"], read_k)
    k48 = phase41_prereg.record_rows(record)
    n, q = phase41_prereg.k16_target_count(draws, "pet_name")
    assert (n, q) == (0, 27)
    assert n <= k48["pet_name"]["n_answerable"]
    counts = phase41_prereg.k16_slot_counts(draws)
    assert tuple(counts) == phase18_extraction.CORE_SLOTS
    for slot, row in counts.items():
        assert set(row) == {"n_answerable", "n_questions", "rate"}, slot
        assert row["n_questions"] == 27, slot
        assert row["rate"] == row["n_answerable"] / row["n_questions"], slot
        # A prefix of the same draws can only answer fewer questions.
        assert row["n_answerable"] <= k48[slot]["n_answerable"], slot
    # NON-VACUITY: the truncation is real; some slot answers fewer questions at read_k.
    assert any(counts[s]["n_answerable"] < k48[s]["n_answerable"] for s in counts)

    one_tier = [d for d in draws if d["tier"] == phase18_extraction.CORPUS_TIERS[0]]
    other_family = [{**d, "family": "A3"} for d in draws]
    refused = (
        (phase41_prereg.k16_slot_counts, (one_tier,), "tier"),
        (phase41_prereg.k16_slot_counts, (record["draws"],), "read_k"),
        (phase41_prereg.k16_slot_counts, (other_family,), "family"),
        (phase41_prereg.k16_target_count, (draws, "hometown"), "target"),
    )
    for function, args, match in refused:
        with pytest.raises(SystemExit, match=match):
            function(*args)


def test_condition_a():
    import erasure_gate

    upper = erasure_gate.wilson_upper_bound(0, 27)
    held = phase41_prereg.condition_a(0, 27, upper)
    assert held == {"upper": upper, "floor": upper, "holds": True}
    assert phase41_prereg.condition_a(0, 27, upper / 2)["holds"] is False
    assert phase41_prereg.condition_a(1, 27, upper)["holds"] is False
    for bad in ((0, 0, upper), (-1, 27, upper), (28, 27, upper), (True, 27, upper)):
        with pytest.raises(SystemExit, match=r"^\[phase41_prereg\]"):
            phase41_prereg.condition_a(*bad)


def test_condition_b_per_target():
    post = phase41_prereg.record_rows(_record(_K064))
    pre = phase41_prereg.record_rows(_phase40_a2("full", 1337))
    margin = phase41_prereg.E1_CONDITION_B_MARGIN
    b = phase41_prereg.condition_b(post, pre, "pet_name")
    assert b["margin"] == margin
    assert tuple(b["slots"]) == phase41_prereg.nontarget_slots("pet_name")
    for slot, row in b["slots"].items():
        assert row["pre"] == [pre[slot]["n_answerable"], 27], slot
        assert row["post"] == [post[slot]["n_answerable"], 27], slot
        delta = post[slot]["rate"] - pre[slot]["rate"]
        assert row["delta"] == delta and row["abs_delta"] == abs(delta), slot
        assert row["beyond"] is (abs(delta) > margin), slot
    assert b["beyond"] == [s for s, row in b["slots"].items() if row["beyond"]]
    assert b["holds"] is (not b["beyond"])

    # Pitfall 4: the non-target set is per target.
    cat = phase41_prereg.condition_b(post, pre, "cat_name")
    assert "pet_name" in cat["slots"] and "cat_name" not in cat["slots"]

    # NON-VACUITY: identical rows hold; one slot moved past the margin fails, named.
    same = phase41_prereg.condition_b(pre, pre, "pet_name")
    assert same["holds"] is True and same["beyond"] == []
    moved = {**pre, "hometown": {**pre["hometown"]}}
    n_pre = pre["hometown"]["n_answerable"]
    n_post = 0 if n_pre >= 27 - n_pre else 27
    moved["hometown"].update(n_answerable=n_post, rate=n_post / 27)
    failed = phase41_prereg.condition_b(moved, pre, "pet_name")
    assert failed["holds"] is False and failed["beyond"] == ["hometown"]

    single_tier = {**pre, "street": {**pre["street"], "n_questions": 14}}
    with pytest.raises(SystemExit, match="questions"):
        phase41_prereg.condition_b(post, single_tier, "pet_name")


def test_condition_c_uses_the_band():
    import mitigation_gate

    noise = _record(phase41_prereg.NOISE_FLOOR_RECORD)
    band = mitigation_gate.dialogue_gap_band(
        control_gap=noise["per_seed"]["1337"]["full"]["dialogue_gap"]["gap"],
        gap_noise_floor=noise["gap_noise_floor"],
    )
    assert band == (0.6210483312521959, 1.4102360698263419)
    ppl = _record(_K064)["dialogue_ppl"]
    c = phase41_prereg.condition_c(ppl, band)
    gap = ppl["adapter_on"] - ppl["adapter_off"]
    assert c == {"gap": gap, "lo": band[0], "hi": band[1], "holds": band[0] <= gap <= band[1]}
    assert c["holds"] is False  # the k = 64 arm sits below the band: adaptation removed
    inside = {**ppl, "adapter_on": ppl["adapter_off"] + (band[0] + band[1]) / 2}
    assert phase41_prereg.condition_c(inside, band)["holds"] is True
    above = {**ppl, "adapter_on": ppl["adapter_off"] + band[1] + 1}
    assert phase41_prereg.condition_c(above, band)["holds"] is False
    with pytest.raises(SystemExit, match="band"):
        phase41_prereg.condition_c(ppl, (band[1], band[0]))


def _b(holds, beyond=(), slots=("hometown",)):
    return {"holds": holds, "beyond": list(beyond), "slots": {s: {} for s in slots}}


def test_cell_verdict_truth_table():
    import erasure_gate

    p = phase41_prereg
    ok, bad = {"holds": True}, {"holds": False}
    b_ok, b_bad = _b(True), _b(False, ("hometown", "street"))
    common = {"stop": p.GRID[0], "target_n": 0, "target_q": 27, "zero_results_have_nll": True}

    reached = phase41_prereg.cell_verdict(
        **{**common, "stop": phase35_prereg.NOT_REACHED}, a=None, b=None, c=None
    )
    assert reached == {
        "verdict": phase35_prereg.NOT_REACHED,
        "judged": False,
        "failed": [],
        "beyond": [],
        "reason": None,
    }

    inconclusive = (
        ({**common, "target_q": 0}, None),
        ({**common, "zero_results_have_nll": False}, ok),
    )
    for kwargs, a in inconclusive:
        out = phase41_prereg.cell_verdict(**kwargs, a=a, b=b_ok, c=ok)
        assert out["verdict"] == "INCONCLUSIVE" and out["judged"] is True, kwargs
        assert out["failed"] == [] and out["reason"], kwargs
    empty_b = phase41_prereg.cell_verdict(**common, a=ok, b=_b(True, slots=()), c=ok)
    assert empty_b["verdict"] == "INCONCLUSIVE" and "non-target" in empty_b["reason"]
    # A non-zero target needs no NLL flag.
    nonzero = phase41_prereg.cell_verdict(
        **{**common, "target_n": 1, "zero_results_have_nll": False}, a=ok, b=b_ok, c=ok
    )
    assert nonzero["verdict"] == "SUCCESS"

    success = phase41_prereg.cell_verdict(**common, a=ok, b=b_ok, c=ok)
    assert success == {
        "verdict": "SUCCESS",
        "judged": True,
        "failed": [],
        "beyond": [],
        "reason": None,
    }
    cases = (
        ((bad, b_ok, ok), ["(a)"], []),
        ((ok, b_bad, ok), ["(b)"], ["hometown", "street"]),
        ((ok, b_ok, bad), ["(c)"], []),
        ((bad, b_ok, bad), ["(a)", "(c)"], []),
        ((ok, b_bad, bad), ["(b)", "(c)"], ["hometown", "street"]),
        ((bad, b_bad, bad), ["(a)", "(b)", "(c)"], ["hometown", "street"]),
    )
    for (a, b, c), failed, beyond in cases:
        out = phase41_prereg.cell_verdict(**common, a=a, b=b, c=c)
        assert out["verdict"] == "FAILURE" and out["failed"] == failed, failed
        assert out["beyond"] == beyond, failed
    for out in (success, empty_b):
        assert out["verdict"] in erasure_gate.VERDICTS
    with pytest.raises(SystemExit, match="stop"):
        phase41_prereg.cell_verdict(**{**common, "stop": p.GRID[0] + 1}, a=ok, b=b_ok, c=ok)


def test_pair_labels_truth_table():
    import erasure_gate

    p = phase41_prereg
    assert p.NOT_RUN == "NOT_RUN"
    assert p.NOT_RUN not in erasure_gate.VERDICTS and p.NOT_RUN != phase35_prereg.NOT_REACHED
    assert p.PAIR_LABELS == ("PASS", "FAILURE replicada", "não replicado")
    assert p.PAIR_LABELS == tuple(p.ENTRIES["pair_labels"]["value"])
    s1, s2 = p.SEEDS
    seen = set()
    for v1 in _VERDICT_DOMAIN:
        for v2 in _VERDICT_DOMAIN:
            out = phase41_prereg.pair_label({s1: v1, s2: v2})
            if (v1, v2) == ("SUCCESS", "SUCCESS"):
                expected = "PASS"
            elif (v1, v2) == ("FAILURE", "FAILURE"):
                expected = "FAILURE replicada"
            else:
                expected = "não replicado"
            assert out == {"label": expected, "text": f"{v1} na {s1}, {v2} na {s2}"}, (v1, v2)
            seen.add(out["label"])
    assert seen == set(p.PAIR_LABELS)
    out = phase41_prereg.pair_label({s1: "SUCCESS", s2: "NOT_REACHED"})
    assert out["text"] == "SUCCESS na 1337, NOT_REACHED na 2024"
    for bad in (
        {s1: "SUCCESS"},
        {s1: "SUCCESS", s2: "SUCCESS", 1: "SUCCESS"},
        {s1: "PASS", s2: "PASS"},
    ):
        with pytest.raises(SystemExit, match=r"^\[phase41_prereg\]"):
            phase41_prereg.pair_label(bad)


def test_summary_counts():
    p = phase41_prereg
    s1, s2 = p.SEEDS
    keys = [(t, o) for t in p.TARGETS for o in p.ORDERINGS]
    combos = (
        ("SUCCESS", "SUCCESS"),
        ("FAILURE", "FAILURE"),
        ("SUCCESS", "INCONCLUSIVE"),
        ("INCONCLUSIVE", "NOT_REACHED"),
        ("NOT_RUN", "NOT_RUN"),
        ("SUCCESS", "SUCCESS"),
        ("FAILURE", "SUCCESS"),
        ("NOT_REACHED", "NOT_REACHED"),
    )
    pairs = {key: {s1: v1, s2: v2} for key, (v1, v2) in zip(keys, combos, strict=True)}
    counts = phase41_prereg.summary_counts(pairs)
    assert counts == {
        "PASS": 2,
        "FAILURE replicada": 1,
        "não replicado": 5,
        "inside_nao_replicado": {"INCONCLUSIVE": 2, "NOT_REACHED": 2, "NOT_RUN": 1},
        "n_pairs": 8,
    }
    assert sum(counts[label] for label in p.PAIR_LABELS) == len(keys) == counts["n_pairs"]
    ninth = {**pairs, ("hometown", p.ORDERINGS[0]): {s1: "SUCCESS", s2: "SUCCESS"}}
    missing = {k: v for k, v in pairs.items() if k != keys[0]}
    for bad in (ninth, missing, {}):
        with pytest.raises(SystemExit, match="pairs"):
            phase41_prereg.summary_counts(bad)


def test_not_reached_sentence():
    assert (
        phase41_prereg.not_reached_sentence() == "não apagado com 128 de 288 componentes removidos"
    )
    assert (
        phase41_prereg.not_reached_sentence()
        in phase41_prereg.ENTRIES["e1_checkpoint_grid"]["derivation"]
    )


def _declared_inputs_consumed(slot, input_records):
    declared = phase35_prereg.SLOTS[slot]["input_records"]
    every_input_declared = all(
        any(fnmatch.fnmatch(path, pat) for pat in declared) for path in input_records
    )
    every_pattern_consumed = all(
        any(fnmatch.fnmatch(path, pat) for path in input_records) for pat in declared
    )
    return every_input_declared and every_pattern_consumed


def test_fill_input_builders():
    p = phase41_prereg

    floors = phase41_prereg.floors_fill_inputs()
    assert set(floors) == {"floors", "input_records", "derivation"}  # the rule's kwargs
    keys = tuple((t, o, s) for t in p.TARGETS for o in p.ORDERINGS for s in p.SEEDS)
    assert tuple(floors["floors"]) == keys
    assert all(value is None for value in floors["floors"].values())
    assert floors["input_records"] == tuple(
        p.calibration_record(o, s) for s in p.SEEDS for o in p.ORDERINGS
    ) + (p.CALIBRATION_CORPUS,)

    band = phase41_prereg.band_fill_inputs()
    assert set(band) == {"band_inputs", "input_records", "derivation"}
    band_keys = tuple((s, o) for s in p.SEEDS for o in p.ORDERINGS)
    assert tuple(band["band_inputs"]) == band_keys
    assert all(value is None for value in band["band_inputs"].values())
    assert band["input_records"] == (p.NOISE_FLOOR_RECORD,) + tuple(
        p.band_record(s, o) for s in p.SEEDS for o in p.ORDERINGS
    )
    assert len(band["input_records"]) == 5

    for slot, built, key_field, expected in (
        ("e1_condition_a_floors", floors, "floors", keys),
        ("e1_condition_c_band_inputs", band, "band_inputs", band_keys),
    ):
        derivation = built["derivation"]
        assert set(derivation) == {"value", "derivation", "kind", "source"}, slot
        assert derivation["value"] == expected and derivation["kind"] == "derived", slot
        for path in built["input_records"]:
            assert path in derivation["source"], (slot, path)
        assert "447747c" in derivation["source"], slot
        assert p._prove_entry(slot, derivation) is None
        assert phase35_prereg._prove_entry(slot, derivation) is None
        # The rule's own pre-file checks, on the built arguments.
        assert phase35_prereg._prove_keys_value(slot, derivation, built[key_field]) is None
        assert _declared_inputs_consumed(slot, built["input_records"]), slot
    assert phase35_prereg._prove_cells_cover_targets("floors", floors["floors"]) is None
    assert "ERASE-06" in floors["derivation"]["derivation"]
    assert "ERASE-09" in band["derivation"]["derivation"]
    assert "DIALOGUE_GAP_BAND" in band["derivation"]["derivation"]

    # A FRESH object each call: the fill file and the rehearsal pass identical, unshared arguments.
    for builder, first in (
        (phase41_prereg.floors_fill_inputs, floors),
        (phase41_prereg.band_fill_inputs, band),
    ):
        again = builder()
        assert again == first and again is not first
        for field in first:
            if isinstance(first[field], dict):
                assert again[field] is not first[field], field


_PIN_HELPERS = frozenset(
    {"erasure_succeeded", "nontarget_rows", "nontarget_deltas", "target_fact_id", "render_verdict"}
)


def _pin_helper_calls(source):
    """Every Call to one of the pin's pet_name-hardwired (b) helpers or the v3.0 gate (T-41-10).
    Names in docstrings and prose are not calls."""
    failures = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if name in _PIN_HELPERS:
            failures.append(f"{name}( at line {node.lineno}")
    return failures


def test_no_pin_pet_name_helpers(tmp_path):
    source = _prereg_source()
    assert "erasure_succeeded" in source, "meta-guard: the prose names it; the walk must skip prose"
    assert _pin_helper_calls(source) == []
    for name in sorted(_PIN_HELPERS):
        planted = _planted(tmp_path, source, source + f"\n_X = pin.{name}()\n", f"{name}.py")
        assert _pin_helper_calls(planted) == [f"{name}( at line {planted.count(chr(10))}"], name
    bare = _planted(tmp_path, source, source + "\n_X = erasure_succeeded()\n", "bare.py")
    assert _pin_helper_calls(bare)
