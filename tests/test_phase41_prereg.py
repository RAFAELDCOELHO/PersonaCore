"""Plan 41-02: the Phase 41 pre-registration, fill file 1 (ERASE-04, ERASE-07 fills; ERASE-03, -05,
-06, -09, -10 written as entries), CPU-only.

What this file proves:
- the record paths are read from the Phase 35 registry, ORDERINGS is ("greedy", the filled
  alternative ordering), and the three fills that must precede every results/phase41_* record
  (e1_checkpoint_grid, e1_alternative_ordering, e1_condition_b_margin) are the registry's objects;
- the caps check runs at import with the grid's count only, never a K = 48 confirmation count.

It reads only tracked files and git history and writes nothing under results/.
"""

import ast
import collections.abc
import fnmatch
import json
import pathlib
import re
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

from test_phase29_prereg import _git  # noqa: E402

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
        p.calibration_record("greedy", 1337) == "results/phase41_calibration_greedy_seed1337.json"
    )
    assert p.band_record(2024, "gradient") == "results/phase41_band_inputs_gradient_seed2024.json"
    assert (
        p.cell_record("cat_name", "greedy", 1337)
        == "results/phase41_cell_cat_name_greedy_seed1337.json"
    )
    assert (
        p.k16_record("pet_name", "gradient", 2024, 48)
        == "results/phase41_k16_pet_name_gradient_seed2024_k048.json"
    )
    assert (
        p.k48_record("street", "greedy", 1337, 128)
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
