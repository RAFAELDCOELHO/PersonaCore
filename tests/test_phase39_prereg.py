"""Plan 39-01: the Phase 39 pre-registration (CTX-01, CTX-03 groundwork, SC4), CPU-only.

What this file proves:
- the record paths, the eight A2 record pins and the D-11/D-26/D-30 approval arithmetic are the
  committed budget's arithmetic and the tracked bytes, never typed;
- the twenty entries and both fills (e6_entry_subset, e6_decomposition_rule);
- scripts/phase39_prereg.py is frozen before every results/phase39_* record, the paths resolve from
  the modules that own them, nothing derived is typed, the entries have four fields and honest
  kinds, importing it opens no checkpoint, it passes the slot census, this file has zero skips and
  every prereg function is called by a CPU test.

It reads only tracked files and git history and writes nothing under results/.
"""

import ast
import fnmatch
import hashlib
import inspect
import json
import os
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
import phase36_prereg  # noqa: E402  (same)
import phase38_prereg  # noqa: E402  (same)
import phase39_prereg  # noqa: E402  (same)

from test_phase29_prereg import _assert_frozen_before, _git, _planted  # noqa: E402
from test_phase35_prereg import (  # noqa: E402
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

PREREG = "scripts/phase39_prereg.py"


def _record(rel):
    return json.loads((_ROOT / rel).read_text(encoding="utf-8"))


def _budget():
    return _record("results/phase36_budget.json")


def _formula(adapters, anchor_adapters, extra_nlls=0):
    """The budget's E6 term (scripts/phase36_budget.py), re-stated here, plus extra NLLs."""
    budget = _budget()
    p, c = budget["unit_prices"], budget["unit_caps"]["E6"]
    full_k = phase35_prereg.FULL_FIDELITY_K
    return (
        adapters
        * (
            p["adapter_setup_high"]
            + c["a2_regenerated_entries"] * p["a2_question_k48_high"] * c["max_k"] / full_k
            + (c["entries"] + c["anchor_slots"])
            * p["e5_candidates_per_slot_max"]
            * p["e5_nll_high"]
        )
        + anchor_adapters * c["anchor_slots"] * c["max_k"] * p["e6_anchor_draw_high"]
    ) / 3600 + extra_nlls * p["e5_nll_high"] / 3600


# =================================================================================================
# (1) PATHS, READINGS, THE A2 PINS AND THE D-11 / D-26 / D-30 ARITHMETIC.
# =================================================================================================


def test_arithmetic_is_the_committed_formula():
    budget = _budget()
    caps = budget["unit_caps"]["E6"]
    assert phase39_prereg.e6_projection_hours(7, 7) == budget["front_hours"]["E6"]
    assert _formula(7, 7) == budget["front_hours"]["E6"]
    assert (
        phase39_prereg.e6_projection_hours(caps["adapters"], caps["anchor_adapters"])
        == (budget["front_hours"]["E6"])
    )
    priced = _formula(8, 8, 8 * 216 * 7 + 8 * 8 * 8)
    actual = _formula(8, 8, 8 * 216 * 7 + 8 * 56)
    stop = phase36_prereg.ENTRIES["front_stop_factor"]["value"] * budget["front_hours"]["E6"]
    assert phase39_prereg.E6_PROJECTION_HOURS == priced
    assert phase39_prereg.E6_PROJECTION_HOURS_ACTUAL_GATE == actual
    assert phase39_prereg.E6_STOP_HOURS == stop
    assert repr(phase39_prereg.E6_PROJECTION_HOURS) == "0.7293568082878159"
    assert repr(phase39_prereg.E6_PROJECTION_HOURS_ACTUAL_GATE) == "0.7285258345864714"
    assert repr(phase39_prereg.E6_STOP_HOURS) == "0.7424221732238463"
    assert phase39_prereg.E6_PROJECTION_HOURS <= phase39_prereg.E6_STOP_HOURS
    assert phase39_prereg.E6_PROJECTION_HOURS_ACTUAL_GATE <= phase39_prereg.E6_STOP_HOURS


def test_arithmetic_extra_nll_counts():
    assert phase39_prereg.N_ENTRIES == 216
    assert phase39_prereg.MINTED_SET_SIZE == 8
    assert phase39_prereg.MINTED_EXTRA_NLLS == 8 * 216 * 7
    assert phase39_prereg.GATE_EXTRA_NLLS_PRICED == 8 * 8 * 8
    assert phase39_prereg.GATE_EXTRA_NLLS_ACTUAL == 8 * 56
    assert phase39_prereg.A2_REGENERATED_ENTRIES == 0
    assert phase39_prereg.APPROVED_E6_ADAPTERS == len(phase39_prereg.READINGS) == 8
    assert phase39_prereg.COMMITTED_ADAPTER_CAP == len(phase39_prereg.PREFIXES) + 1 == 7
    assert phase39_prereg.COMMITTED_ANCHOR_ADAPTER_CAP == len(phase39_prereg.PREFIXES) + 1


def test_arithmetic_reference_total_is_the_committed_sets():
    import phase18_extraction  # torch at import: inside the test only

    sizes = [len(phase18_extraction.reference_set_for(s)) for s in phase38_prereg.SLOTS]
    assert sizes == [8, 8, 7, 7, 7, 6, 7, 6]
    assert phase39_prereg._reference_total() == sum(sizes) == 56


def test_arithmetic_approval_block_is_fresh_and_reproduces_each_step():
    budget = _budget()
    first = phase39_prereg.approval_block()
    json.dumps(first)
    assert first["ruling"] == phase39_prereg.D11_RULING
    assert first["d26_ruling"] == phase39_prereg.D26_RULING == "Yes, add adapter-off"
    assert first["approved_adapters"] == 8
    assert first["committed_adapter_cap"] == first["committed_anchor_adapter_cap"] == 7
    assert first["readings"] == list(phase38_prereg.READINGS)
    assert first["reference_reading"] == "k0"
    assert first["cell_readings"] == list(phase39_prereg.CELL_READINGS)
    assert first["descriptive_readings"] == ["adapter_off"]
    steps = dict(first["projection_steps"])
    assert repr(steps["d11"]) == "0.7030772649827931"
    assert steps["d11"] == _formula(8, 8, 7 * 216 * 7)
    assert repr(steps["d26"]) == "0.7227090186770592"
    assert steps["d26"] == _formula(8, 8, 8 * 216 * 7)
    assert steps["d30_priced"] == phase39_prereg.E6_PROJECTION_HOURS
    assert steps["d30_actual_gate"] == phase39_prereg.E6_PROJECTION_HOURS_ACTUAL_GATE
    assert first["e6_projection_hours"] == phase39_prereg.E6_PROJECTION_HOURS
    assert first["committed_front_hours_e6"] == budget["front_hours"]["E6"]
    assert first["e6_stop_hours"] == phase39_prereg.E6_STOP_HOURS
    assert first["not_measured"] == list(phase39_prereg.NOT_MEASURED)
    assert first["budget_record"] == "results/phase36_budget.json"
    assert first["untouched"] == [
        "ledger/v6_mps_ledger.jsonl",
        "results/phase36_budget.json",
        "scripts/phase36_ledger.py",
        "scripts/phase36_caps.py",
    ]
    import phase36_ledger

    # IN-04: the paths that have an owning constant come from it.
    assert first["untouched"][:2] == [phase36_ledger.LEDGER_PATH, phase39_prereg.BUDGET_RECORD]
    first["readings"].append("planted")
    first["not_measured"].clear()
    first["projection_steps"]["d11"] = 0.0
    second = phase39_prereg.approval_block()
    assert second["readings"] == list(phase38_prereg.READINGS)
    assert second["not_measured"] == list(phase39_prereg.NOT_MEASURED)
    assert second["projection_steps"]["d11"] == steps["d11"] == _formula(8, 8, 7 * 216 * 7)


def test_records_are_the_phase39_paths():
    assert phase39_prereg.RECORDS == ("results/phase39_ctx.json", "results/phase39_ctx_report.md")
    assert phase39_prereg.RECORD_GLOB == "results/phase39_*"
    for path in phase39_prereg.RECORDS:
        assert fnmatch.fnmatch(path, "results/phase39_*")
    assert (phase39_prereg.CTX_RECORD, phase39_prereg.REPORT_RECORD) == phase39_prereg.RECORDS
    assert phase39_prereg.BUDGET_RECORD == phase38_prereg.BUDGET_RECORD


def _head_sha256(path):
    blob = subprocess.run(
        ("git", "show", f"HEAD:{path}"), cwd=_ROOT, capture_output=True, check=True
    ).stdout
    return hashlib.sha256(blob).hexdigest()


def test_a2_sha_pins_match_the_tracked_bytes():
    pins = phase39_prereg.A2_RECORDS
    assert tuple(pins) == phase38_prereg.READINGS
    for reading, pin in pins.items():
        assert set(pin) == {"path", "sha256"}, reading
        assert _head_sha256(pin["path"]) == pin["sha256"], reading
    assert pins["k0"]["path"] == phase38_prereg.ADAPTER_ON_RECORD
    assert pins["k78"]["path"] == phase38_prereg.ERASED_RECORD
    assert pins["M2"]["path"] == phase38_prereg.RETRAIN_RECORD
    assert pins["adapter_off"]["path"] == phase38_prereg.ADAPTER_OFF_RECORD
    assert pins["adapter_off"]["sha256"] == phase39_prereg.ADAPTER_OFF_SHA256
    assert len({pin["path"] for pin in pins.values()}) == len(pins)


def test_a2_sha_seven_pins_parse_from_the_budget_ruling():
    ruling = _budget()["cap_rulings"]["E6.a2_regenerated_entries"]
    for reading in phase39_prereg.CTX02_READINGS:
        pin = phase39_prereg.A2_RECORDS[reading]
        assert pin["path"] in ruling and pin["sha256"] in ruling, reading
    assert phase39_prereg.ADAPTER_OFF_SHA256 not in ruling


def test_readings_split_into_reference_cells_and_descriptive():
    assert phase39_prereg.READINGS is phase38_prereg.READINGS
    assert phase39_prereg.PREFIXES is phase38_prereg.PREFIXES
    assert phase39_prereg.SLOTS is phase38_prereg.SLOTS
    assert phase39_prereg.MARGIN is phase38_prereg.MARGIN
    assert phase39_prereg.K == phase35_prereg.FULL_FIDELITY_K
    assert phase39_prereg.REFERENCE_READING == "k0"
    assert phase39_prereg.DESCRIPTIVE_READINGS == ("adapter_off",)
    assert phase39_prereg.CTX02_READINGS == ("k0", "k8", "k16", "k32", "k64", "k78", "M2")
    assert phase39_prereg.CELL_READINGS == ("k8", "k16", "k32", "k64", "k78", "M2")
    assert phase39_prereg.N_QUESTIONS == 27
    assert phase39_prereg.CELL_PREFIX_READINGS == ("k8", "k16", "k32", "k64", "k78")
    assert phase39_prereg.RETRAIN_READING == "M2"
    assert phase39_prereg.M2_LABEL in phase39_prereg.ENTRIES["e6_decomposition_rule"]["value"]["m2"]
    assert phase39_prereg.EVENTS == ("collapse", "damage")
    assert phase39_prereg.CLASSES == (
        "CONTEXT_SUFFICIENT",
        "INSTRUMENT_SUFFICIENT",
        "EITHER",
        "INTERACTION_ONLY",
        "NO_DISAGREEMENT",
    )


def test_wr01_outcomes_are_phase38_relation_outcomes():
    assert phase39_prereg.STATUSES == ("INTACT", "LOST", "UNREACHABLE_AT_SIZE", "ALREADY_AT_K0")
    returned = (
        phase38_prereg.relation(None, None, reachable=False),
        phase38_prereg.relation(0, 8),
    )
    assert phase39_prereg.WR01_OUTCOMES == returned


def test_not_measured_names_both_readings():
    first, second = phase39_prereg.NOT_MEASURED
    assert "|R| > 8" in first and "D-12" in first
    assert "B1'" in second and "D-23d" in second


# =================================================================================================
# (2) THE ENTRIES AND BOTH FILLS.
# =================================================================================================

_ENTRY_NAMES = {
    "e6_entry_subset",
    "e6_decomposition_rule",
    "anchor_context",
    "anchor_generation",
    "question_context",
    "per_token_nll",
    "taught_suffix_nll",
    "rank_with_question",
    "common_unit",
    "predicted_hit_rate",
    "gate_exact_ranks",
    "gate_a2_counts",
    "cpu_crosscheck",
    "descriptive_extras",
    "not_measured",
    "run_shape",
    "limitations",
    "e6_projection_hours",
    "e6_projection_hours_actual_gate",
    "e6_stop_hours",
}
_DERIVED = {"e6_projection_hours", "e6_projection_hours_actual_gate", "e6_stop_hours"}
# Keyed by ENTRY NAME, never by D-ID: cpu_crosscheck also cites D-30a and carries no label. Plan
# 39-03 moved each name from the plan-time default label to Rafael's dated confirmation.
_RULINGS_DATE = "2026-10-05"
_CONFIRMED = {
    "run_shape": ("D-27", _RULINGS_DATE),
    "anchor_generation": ("D-28", _RULINGS_DATE),
    "predicted_hit_rate": ("D-29", _RULINGS_DATE),
    "taught_suffix_nll": ("D-30a", _RULINGS_DATE),
}
# The 39-REVIEW.md item quoted in each confirmed entry.
_CONFIRMED_ITEM = {
    "run_shape": "a",
    "anchor_generation": "b",
    "predicted_hit_rate": "c",
    "taught_suffix_nll": "d",
}
_REVIEW_PATH = ".planning/phases/39-instrument-context-2-2/39-REVIEW.md"
_REVIEW_RULINGS_COMMIT = "cf51309"


def _review_quotes():
    """{item: quote} of 39-REVIEW.md's Resolution items a-j at the commit that recorded them."""
    import re

    text = _git("show", f"{_REVIEW_RULINGS_COMMIT}:{_REVIEW_PATH}")
    return {m[0]: m[1] for m in re.findall(r'^([a-j])\. "(.*)"$', text, re.MULTILINE)}


def _unconfirmed(entries):
    """The entry names whose derivation still carries a plan-time default or a pending check."""
    return [
        name
        for name, entry in entries.items()
        if "not yet confirmed" in entry["derivation"] or "to be confirmed" in entry["derivation"]
    ]


def test_e6_entry_subset_is_every_a2_entry():
    import phase36_caps

    subset = phase39_prereg.E6_ENTRY_SUBSET
    assert type(subset) is tuple
    assert subset == tuple(range(len(phase35_prereg.a2_corpus_entries())))
    assert subset == tuple(range(216))
    assert phase36_caps.counts_for("e6_entry_subset", subset) == {"entries": 216}
    entry = phase39_prereg.ENTRIES["e6_entry_subset"]
    assert entry["value"] == subset and type(entry["value"]) is tuple
    for path in (phase38_prereg.PROBE_E1_RECORD, phase39_prereg.PROBE_E6_RECORD):
        assert path in entry["source"]
    assert "D-01" in entry["derivation"] and "STOP" in entry["derivation"]


def test_fill_decomposition_rule_equals_the_entry():
    filled = phase39_prereg.E6_DECOMPOSITION_RULE
    entry = phase39_prereg.ENTRIES["e6_decomposition_rule"]
    assert set(filled) == {"value", "derivation", "kind", "source"}
    for field in ("derivation", "kind", "source"):
        assert filled[field] == entry[field], field
    value = filled["value"]
    assert set(value) == set(entry["value"])
    assert value["reference_reading"] == phase39_prereg.REFERENCE_READING
    assert value["cell_readings"] == phase39_prereg.CELL_READINGS
    assert value["descriptive_readings"] == phase39_prereg.DESCRIPTIVE_READINGS
    assert "never a cell" in value["cells"] and "baseline" in value["cells"]
    assert value["events"] == phase39_prereg.EVENTS
    assert value["statuses"] == phase39_prereg.STATUSES
    assert value["classes"] == phase39_prereg.CLASSES
    assert set(value["readings"]) == {"R_a", "R_q", "G_a", "G_q"}
    assert set(value["lost"]) == {"R_a", "collapse", "damage"}
    assert "MARGIN" in value["margin"] and "MARGIN" in value["lost"]["damage"]
    assert "strict >" in value["lost"]["damage"]
    assert value["disagreement"] == "R_a INTACT and G_q LOST"
    precedence = " ".join(value["precedence"])
    for name in phase39_prereg.CLASSES + phase39_prereg.WR01_OUTCOMES:
        assert name in precedence, name
    assert "D-33" in value["ties"]
    assert "adapter-off" in value["never_classified"]
    for d_id in ("D-13", "D-14", "D-15", "D-16", "D-24", "D-25", "D-33"):
        assert d_id in filled["derivation"], d_id
    for item in "efghij":
        assert phase39_prereg.RULINGS[item] in filled["derivation"], item
    assert "REVERSE_DISAGREEMENT" in value["reverse_disagreement"]


def test_entries_are_the_twenty_names_with_honest_kinds():
    kinds = {name: entry["kind"] for name, entry in phase39_prereg.ENTRIES.items()}
    assert set(kinds) == _ENTRY_NAMES
    assert len(kinds) == len(_ENTRY_NAMES) == 20
    assert {n for n, k in kinds.items() if k == "derived"} == _DERIVED
    assert {n for n, k in kinds.items() if k == "preference"} == _ENTRY_NAMES - _DERIVED
    entries = phase39_prereg.ENTRIES
    assert entries["e6_projection_hours"]["value"] == phase39_prereg.E6_PROJECTION_HOURS
    assert (
        entries["e6_projection_hours_actual_gate"]["value"]
        == phase39_prereg.E6_PROJECTION_HOURS_ACTUAL_GATE
    )
    assert entries["e6_stop_hours"]["value"] == phase39_prereg.E6_STOP_HOURS
    assert entries["descriptive_extras"]["value"] == phase39_prereg.APPROVED_E6_ADAPTERS
    assert entries["not_measured"]["value"] == phase39_prereg.NOT_MEASURED
    assert entries["gate_exact_ranks"]["value"] == phase38_prereg.READINGS
    assert entries["anchor_generation"]["value"]["K"] == phase35_prereg.FULL_FIDELITY_K
    assert type(entries["limitations"]["value"]) is tuple


def test_preferences_are_labelled():
    quotes = _review_quotes()
    assert list(quotes) == list("abcdefghij"), "meta-guard: the Resolution items parsed short"
    assert dict(phase39_prereg.RULINGS) == quotes
    assert phase39_prereg.RULINGS_DATE == _RULINGS_DATE
    entries = phase39_prereg.ENTRIES
    for name, entry in entries.items():
        assert "D-" in entry["derivation"], name
    for name, (d_id, date) in _CONFIRMED.items():
        derivation = entries[name]["derivation"]
        assert d_id in derivation, name
        quote = quotes[_CONFIRMED_ITEM[name]]
        assert f'confirmed by Rafael {date}: "{quote}"' in derivation, name
        assert phase39_prereg._confirmed(_CONFIRMED_ITEM[name]) in derivation, name
    rule = entries["e6_decomposition_rule"]["derivation"]
    for d_id in ("D-25", "D-33"):
        assert d_id in rule, d_id
    for item in "eghij":
        assert f'confirmed by Rafael {_RULINGS_DATE}: "{quotes[item]}"' in rule, item
    assert f'changed by Rafael {_RULINGS_DATE}: "{quotes["f"]}"' in rule
    assert _unconfirmed(entries) == []
    # NON-VACUITY: the plan-time label and the pending-review phrase are both caught.
    planted = {"x": {"derivation": "default taken at plan time, not yet confirmed by Rafael"}}
    assert _unconfirmed(planted) == ["x"]
    assert _unconfirmed({"y": {"derivation": "to be confirmed at the plan-03 review"}}) == ["y"]
    assert not hasattr(phase39_prereg, "_DEFAULT")
    assert "cpu_crosscheck" not in _CONFIRMED
    cpu = entries["cpu_crosscheck"]["derivation"]
    assert "D-30a" in cpu and "confirmed by Rafael" not in cpu


# =================================================================================================
# (3) ANCESTRY (SC4, T-39-01): frozen before every results/phase39_* record. Honest at zero records
# and after them.
# =================================================================================================


def _strictly_before(x, y):
    run = subprocess.run(("git", "merge-base", "--is-ancestor", x, y), cwd=_ROOT, check=False)
    return x != y and run.returncode == 0


def _first_add(path):
    return _git("log", "--diff-filter=A", "--format=%H", "--", path).split()[-1]


def _phase39_records():
    return sorted(_git("ls-files", "results/phase39_*").split())


def test_phase39_prereg_is_frozen_before_every_phase39_record():
    _assert_frozen_before(PREREG, _phase39_records())
    # NON-VACUITY (natural RED): the v6.0 pre-registration was added before this one existed.
    with pytest.raises(subprocess.CalledProcessError):
        _assert_frozen_before(PREREG, ["scripts/phase35_prereg.py"])


def test_this_test_file_is_first_added_before_every_phase39_record():
    # Only the FIRST add: a later fix to this file must not redden the guard forever.
    mine = _first_add("tests/test_phase39_prereg.py")
    for record in _phase39_records():
        assert _strictly_before(mine, _first_add(record)), record
    # NON-VACUITY: the same check against a file added long before this one is False.
    assert not _strictly_before(mine, _first_add("scripts/phase35_prereg.py"))


def test_records_at_commit_is_true_at_the_first_commit():
    first = _git("log", "--format=%H", "--", PREREG).split()[-1]
    at_first = _git("ls-tree", "-r", "--name-only", first, "--", "results/").split()
    assert at_first, "meta-guard: the first commit's results/ tree is empty, the check is vacuous"
    assert not [p for p in at_first if p.startswith("results/phase39_")]
    assert phase39_prereg.RECORDS_AT_COMMIT == 0


def test_input_paths_resolve_from_the_modules():
    declared = phase35_prereg.SLOTS["e6_entry_subset"]["input_records"]
    for path in (phase39_prereg.PROBE_E6_RECORD, phase38_prereg.PROBE_E1_RECORD):
        assert _git("ls-files", "--error-unmatch", path) == path
        assert any(fnmatch.fnmatch(path, pattern) for pattern in declared), path
    assert phase39_prereg.RECORD_GLOB in phase35_prereg.V6_RESULT_PATHS
    assert phase35_prereg.SLOTS["e6_decomposition_rule"]["input_records"] == ()


# =================================================================================================
# (4) THE D-11 AND D-26 RULINGS, QUOTED AT THEIR FIXED COMMITS.
# =================================================================================================

_CONTEXT_PATH = ".planning/phases/39-instrument-context-2-2/39-CONTEXT.md"


def _bullet(commit, prefix):
    """The bullet starting with ``prefix`` plus its continuation lines, joined by ONE space."""
    lines = _git("show", f"{commit}:{_CONTEXT_PATH}").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(prefix))
    bullet = [lines[start].strip()]
    for line in lines[start + 1 :]:
        if not line.strip() or line.strip().startswith("- "):
            break
        bullet.append(line.strip())
    return " ".join(bullet)


def test_d11_ruling_is_quoted_verbatim():
    quote = _bullet("62af2fe", "- **D-11").split('"', 2)[1]
    assert len(quote.split()) > 5, "meta-guard: the D-11 bullet parsed too short"
    assert quote == phase39_prereg.D11_RULING
    assert quote in phase39_prereg.ENTRIES["descriptive_extras"]["derivation"]
    assert phase39_prereg.approval_block()["ruling"] == quote


def test_d26_ruling_is_quoted_verbatim():
    bullet = _bullet("3499c3b", "- **D-26")
    quote = bullet.split('Rafael: "', 1)[1].split('"', 1)[0]
    assert len(quote.split()) > 2, "meta-guard: the D-26 bullet parsed too short"
    assert quote == phase39_prereg.D26_RULING
    assert quote in phase39_prereg.ENTRIES["descriptive_extras"]["derivation"]


# =================================================================================================
# (5) NOTHING DERIVED IS TYPED (T-39-02).
# =================================================================================================


def _smallest_reachable_count(n):
    """The smallest k = 0 count whose drop to 0 is strictly above MARGIN at n units."""
    return next(c for c in range(n + 1) if c / n - 0 / n > phase38_prereg.MARGIN)


def test_no_derived_value_is_typed_in_the_prereg(tmp_path):
    budget = _budget()
    assert _smallest_reachable_count(27) == 9
    steps = phase39_prereg.approval_block()["projection_steps"]
    totals = phase39_prereg.report_k0_totals()
    # WR-05: the D-11 priced minted NLLs, the reference total, the questions per slot, the cells per
    # event and the WR-01 report figures, each computed here.
    new_seeds = {
        phase39_prereg.COMMITTED_ADAPTER_CAP
        * phase39_prereg.N_ENTRIES
        * (phase39_prereg.MINTED_SET_SIZE - 1),
        phase39_prereg._reference_total(),
        len(phase35_prereg.a2_corpus_entries()) // len(phase39_prereg.SLOTS),
        len(phase39_prereg.cells("damage")),
        sum(a for a, _ in totals.values()),
        *(a for a, _ in totals.values()),
        *(n for _, n in totals.values()),
    }
    assert new_seeds >= {10584, 56, 27, 48}, "meta-guard: a WR-05 seed is not the reviewed value"
    seeds = {
        len(phase35_prereg.a2_corpus_entries()),
        phase35_prereg.FULL_FIDELITY_K,
        _smallest_reachable_count(27),
        phase39_prereg.MINTED_EXTRA_NLLS,
        phase39_prereg.GATE_EXTRA_NLLS_PRICED,
        phase39_prereg.GATE_EXTRA_NLLS_ACTUAL,
        *new_seeds,
    }
    new_floats = {steps["d11"], steps["d26"]}
    floats = {
        phase39_prereg.E6_PROJECTION_HOURS,
        phase39_prereg.E6_PROJECTION_HOURS_ACTUAL_GATE,
        phase39_prereg.E6_STOP_HOURS,
        phase38_prereg.MARGIN,
        budget["front_hours"]["E6"],
        budget["unit_prices"]["e5_nll_high"],
        *new_floats,
    }
    assert all(type(f) is float for f in floats), "meta-guard: a census value is not a float"
    real = _ROOT / PREREG
    before = real.read_bytes()
    source = before.decode("utf-8")
    assert _literal_failures(source, seeds, floats, set()) == []
    plants = [
        ("stop.py", f"\nX = {phase39_prereg.E6_STOP_HOURS!r}\n"),
        ("entries.py", f"\nS = {len(phase35_prereg.a2_corpus_entries())!r}\n"),
    ]
    plants += [(f"seed{i}.py", f"\nX = {v!r}\n") for i, v in enumerate(sorted(new_seeds))]
    plants += [(f"float{i}.py", f"\nX = {v!r}\n") for i, v in enumerate(sorted(new_floats))]
    for name, line in plants:
        planted = _planted(tmp_path, source, source + line, name)
        assert _literal_failures(planted, seeds, floats, set()), name
    assert real.read_bytes() == before


# =================================================================================================
# (6) ENTRIES: EXACTLY FOUR FIELDS, NO PROPOSER (T-39-06); THE PRIVATE HELPERS.
# =================================================================================================


def _good_entry():
    return {"value": 1, "derivation": "d", "kind": "derived", "source": "s"}


def test_entries_have_exactly_four_fields_and_no_proposer(tmp_path):
    assert phase39_prereg.ENTRY_FIELDS is phase35_prereg.ENTRY_FIELDS
    assert phase39_prereg.KINDS is phase35_prereg.KINDS
    for name, entry in phase39_prereg.ENTRIES.items():
        assert set(entry) == {"value", "derivation", "kind", "source"}, name
    with pytest.raises(TypeError):
        phase39_prereg.ENTRIES["planted"] = {}
    assert phase39_prereg._prove_entries() is None

    phase39_prereg._prove_entry("ok", _good_entry())
    refused = (
        {**_good_entry(), "proposer": "Rafael"},
        {**_good_entry(), "adopted_by": "Rafael"},
        {k: v for k, v in _good_entry().items() if k != "source"},
        {**_good_entry(), "kind": "guess"},
        {**_good_entry(), "derivation": ""},
        {**_good_entry(), "value": phase39_prereg.FORBIDDEN_PHRASE},
        [1],
    )
    for entry in refused:
        with pytest.raises(SystemExit, match=r"^\[phase39_prereg\]"):
            phase39_prereg._prove_entry("x", entry)

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
        source, first.lineno, first.col_offset + 1, phase39_prereg.FORBIDDEN_PHRASE
    )
    ast.parse(planted_phrase)
    assert _entry_string_failures(_planted(tmp_path, source, planted_phrase, "phrase.py"))
    assert real.read_bytes() == before


def test_prove_and_read():
    with pytest.raises(SystemExit, match=r"^\[phase39_prereg\] x$"):
        phase39_prereg._prove(False, "x")
    assert phase39_prereg._prove(True, "x") is None
    read = phase39_prereg._read(phase39_prereg.BUDGET_RECORD)
    assert isinstance(read, dict) and "unit_caps" in read


# =================================================================================================
# (7) IMPORTING THE PREREG OPENS NO CHECKPOINT; THE SLOT CENSUS, ZERO SKIPS, EVERY FUNCTION CALLED.
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
import phase39_prereg

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
    "every_entry": phase39_prereg.E6_ENTRY_SUBSET == tuple(range(216)),
    "planted": [os.fspath(p) for p in planted],
    "planted_flagged": list(_FLAGGED),
}}))
"""


def test_importing_the_prereg_opens_no_checkpoint(tmp_path):
    """Replaces Phase 38's torch-free probe: this file loads torch through a2_corpus_entries() by
    design (39-RESEARCH M12; precedent 38-05 Deviation 1). An "open" audit hook watches the import.

    Blind spot: safetensors opens files in Rust (safe_open / load_file) without a Python "open"
    audit event, so a safetensors read is invisible to the hook; the sys.modules leg covers it.
    torch.load and every Python-level open are seen.
    """
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
    assert result["every_entry"] is True
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


def test_phase39_scripts_pass_the_slot_census():
    paths = sorted(_SCRIPTS.glob("phase39_*.py"))
    assert paths, "meta-guard: no scripts/phase39_*.py, the census would be vacuous"
    sources = [(p.relative_to(_ROOT).as_posix(), p.read_text(encoding="utf-8")) for p in paths]
    assert _slot_census_failures(sources) == []


def test_no_skips_in_this_file(tmp_path):
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert _skip_failures(source) == []
    planted = source + '\n\ndef test_planted():\n    pytest.skip("x")\n'
    assert _skip_failures(_planted(tmp_path, source, planted, "skip.py"))


def test_census_every_phase39_prereg_function_has_a_cpu_test(tmp_path):
    real = _ROOT / PREREG
    before = real.read_bytes()
    source = before.decode("utf-8")
    test_source = pathlib.Path(__file__).read_text(encoding="utf-8")
    defs = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)]
    assert defs, "meta-guard: the prereg defines no function, the census would be vacuous"
    assert _untested_functions("phase39_prereg", source, test_source) == []

    planted = source + '\n\ndef planted_untested():\n    """Planted."""\n'
    copied = _planted(tmp_path, source, planted, "untested.py")
    assert _untested_functions("phase39_prereg", copied, test_source) == ["planted_untested"]
    assert real.read_bytes() == before


# =================================================================================================
# (8) PLAN 39-02 TASK 1: GATE 2, THE COMMITTED COUNTS, THE D-07 RATES, THE D-17 PREDICTION, THE
# ANCHOR SEED INDEX, THE MINTED MEMBERS AND THE D-23b PREMISE — on the real tracked JSON.
# =================================================================================================

_SLOT_ORDER = (
    "person_name",
    "pet_name",
    "cat_name",
    "sibling_name",
    "hometown",
    "street",
    "birth_year",
    "house_number",
)
# Measured at plan time (39-02-PLAN interfaces), in _SLOT_ORDER. The test holds them, never the
# prereg.
_A2_COUNTS = {
    "k0": (26, 27, 27, 27, 21, 27, 18, 24),
    "k8": (18, 24, 27, 27, 7, 27, 14, 24),
    "k16": (10, 18, 27, 22, 3, 24, 13, 24),
    "k32": (1, 2, 27, 10, 1, 11, 14, 10),
    "k64": (0, 0, 6, 0, 0, 0, 11, 6),
    "k78": (0, 0, 7, 0, 0, 0, 8, 5),
    "M2": (26, 0, 27, 27, 18, 27, 18, 17),
    "adapter_off": (0, 0, 0, 0, 0, 0, 0, 0),
}
_N_QUESTIONS = 27


def _expected_counts():
    return {r: dict(zip(_SLOT_ORDER, row, strict=True)) for r, row in _A2_COUNTS.items()}


def test_gate2_reproduces_every_committed_count():
    assert phase39_prereg.SLOTS == _SLOT_ORDER
    gate = phase39_prereg.gate2()
    json.dumps(gate)
    assert gate["passed"] is True
    assert tuple(gate["rows"]) == phase39_prereg.READINGS
    assert gate["sha256"] == {r: pin["sha256"] for r, pin in phase39_prereg.A2_RECORDS.items()}
    expected = _expected_counts()
    cells = 0
    for reading, rows in gate["rows"].items():
        assert tuple(rows) == _SLOT_ORDER, reading
        for slot, row in rows.items():
            assert row["equal"] is True, (reading, slot)
            assert row["n_questions"] == _N_QUESTIONS, (reading, slot)
            assert row["count"] == row["committed"] == expected[reading][slot], (reading, slot)
            cells += 1
    assert cells == len(phase39_prereg.READINGS) * len(_SLOT_ORDER) == 64


def _copy_a2_records(root):
    import shutil

    for pin in phase39_prereg.A2_RECORDS.values():
        target = root / pin["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(_ROOT / pin["path"], target)


def test_gate2_refuses_a_tampered_record(tmp_path):
    _copy_a2_records(tmp_path)
    # NON-VACUITY: the untampered copies verify.
    assert phase39_prereg.verify_a2_records(root=tmp_path) == {
        r: pin["sha256"] for r, pin in phase39_prereg.A2_RECORDS.items()
    }
    path = tmp_path / phase39_prereg.A2_RECORDS["k32"]["path"]
    data = bytearray(path.read_bytes())
    at = data.index(b'"completions": [') + len(b'"completions": [')
    at = next(i for i in range(at, len(data)) if chr(data[i]).isalpha())
    data[at] = ord("b") if data[at] != ord("b") else ord("c")
    path.write_bytes(bytes(data))
    with pytest.raises(SystemExit, match=r"^\[phase39_prereg\] k32: "):
        phase39_prereg.gate2(root=tmp_path)


def test_gate2_reports_a_count_mismatch(monkeypatch):
    import copy

    real = phase38_prereg.a2_counts()
    off = copy.deepcopy(real)
    off["person_name"]["counts"][8] += 1
    monkeypatch.setattr(phase38_prereg, "a2_counts", lambda: off)
    gate = phase39_prereg.gate2()
    assert gate["passed"] is False
    unequal = [
        (r, s) for r, rows in gate["rows"].items() for s, row in rows.items() if not row["equal"]
    ]
    assert unequal == [("k8", "person_name")]
    assert gate["rows"]["k8"]["person_name"]["committed"] == 19


def test_gate2_target_k0_row_is_independent():
    """WR-01: the erasure target's k0 row is checked against the Phase 18 report's totals."""
    import phase19_erasure

    assert _head_sha256(phase39_prereg.PHASE18_REPORT) == phase39_prereg.PHASE18_REPORT_SHA256
    totals = phase39_prereg.report_k0_totals()
    assert set(totals) == {"core_taught", "core_held_out"}
    k0 = phase39_prereg.committed_a2_counts()["k0"]
    assert sum(n for _, n in totals.values()) == len(phase39_prereg.E6_ENTRY_SUBSET)
    assert sum(a for a, _ in totals.values()) == sum(k0.values())
    target = phase19_erasure.TARGET_SLOT
    assert target == "pet_name"
    gate = phase39_prereg.gate2()
    row = gate["rows"]["k0"][target]
    assert row["independent"] is True and phase39_prereg.PHASE18_REPORT in row["source"]
    assert row["count"] == row["committed"] == k0[target]
    flagged = [
        (r, s) for r, rows in gate["rows"].items() for s, x in rows.items() if "independent" in x
    ]
    assert flagged == [("k0", target)]


def test_gate2_refuses_a_shifted_target_k0(monkeypatch):
    """WR-01's confirmed probe: a -5 shift in the target's re-derived k0 count now fails gate 2."""
    import phase19_erasure
    import phase19_run

    on = _record(phase39_prereg.A2_RECORDS["k0"]["path"])["draws"]
    real = phase19_run._pooled_rows

    def shifted(draws, *args):
        rows = real(draws, *args)
        if draws == on:
            for row in rows.values():
                if row["slot"] == phase19_erasure.TARGET_SLOT:
                    row["n_answerable"] -= 5
        return rows

    monkeypatch.setattr(phase19_run, "_pooled_rows", shifted)
    gate = phase39_prereg.gate2()
    assert gate["passed"] is False
    unequal = [
        (r, s) for r, rows in gate["rows"].items() for s, x in rows.items() if not x["equal"]
    ]
    assert unequal == [("k0", "pet_name")]
    # NON-VACUITY: the same shift slipped through before WR-01 (same scorer on both sides).
    assert (
        phase38_prereg.a2_counts()["pet_name"]["counts"][0]
        == gate["rows"]["k0"]["pet_name"]["count"]
    )


def test_gate2_target_k0_without_a_report_row_is_not_independent(monkeypatch):
    monkeypatch.setattr(phase39_prereg, "report_k0_totals", lambda **_: {})
    target, count, note = phase39_prereg._target_k0_check({"pet_name": 27})
    assert (target, count, note["independent"]) == ("pet_name", None, False)
    assert "SHA-pinned only" in note["source"]
    gate = phase39_prereg.gate2()
    assert gate["passed"] is True
    assert gate["rows"]["k0"]["pet_name"]["independent"] is False


def test_report_k0_totals_refuses_a_tampered_report(tmp_path):
    target = tmp_path / phase39_prereg.PHASE18_REPORT
    target.parent.mkdir(parents=True)
    target.write_bytes((_ROOT / phase39_prereg.PHASE18_REPORT).read_bytes() + b"\n")
    with pytest.raises(SystemExit, match=r"^\[phase39_prereg\] .*WR-01"):
        phase39_prereg.report_k0_totals(root=tmp_path)


def test_a2_sha_verify_records():
    digests = phase39_prereg.verify_a2_records()
    assert digests == {r: pin["sha256"] for r, pin in phase39_prereg.A2_RECORDS.items()}
    assert tuple(digests) == phase39_prereg.READINGS


def test_committed_a2_counts_sources():
    counts = phase39_prereg.committed_a2_counts()
    assert tuple(counts) == phase39_prereg.CTX02_READINGS + phase39_prereg.DESCRIPTIVE_READINGS
    assert counts == _expected_counts()
    assert set(counts["adapter_off"].values()) == {0}
    scores = _record(phase38_prereg.RETRAIN_SCORES)["retrain_scores"]
    m2 = {row["slot"]: row["m2_answerable"] for row in scores["retained"].values()}
    m2[scores["omitted_fact"]["slot"]] = scores["omitted_fact"]["successes"]
    assert counts["M2"] == m2
    a2 = phase38_prereg.a2_counts()
    for k in phase39_prereg.PREFIXES:
        assert counts[f"k{k}"] == {s: a2[s]["counts"][k] for s in _SLOT_ORDER}, k


def test_values_are_the_locked_facts():
    import phase14_factset

    values = phase39_prereg._values()
    assert values == {f.id: f.value for f in phase14_factset.LOCKED_FACTS}
    assert len(values) == len(_SLOT_ORDER)


def test_draw_rate_bounds_and_labels():
    import erasure_gate
    import phase20_gate_coverage

    zero = phase39_prereg.draw_rate(0, 48)
    json.dumps(zero)
    assert zero["rate"] == 0.0 and zero["wilson_lower_95"] == 0.0
    assert zero["wilson_upper_95"] == erasure_gate.wilson_upper_bound(0, 48)
    assert zero["unit"] == "draw" and zero["descriptive"] is True
    assert "D-07" in zero["note"] and "clustering" in zero["note"]
    full = phase39_prereg.draw_rate(1296, 1296)
    assert full["rate"] == 1.0 and full["wilson_upper_95"] == 1.0
    some = phase39_prereg.draw_rate(7, 48)
    assert some["successes"] == 7 and some["n"] == 48 and some["rate"] == 7 / 48
    assert some["wilson_lower_95"] == phase20_gate_coverage.wilson_lower_bound(7, 48)
    assert some["wilson_lower_95"] < some["rate"] < some["wilson_upper_95"]


def test_draw_rate_unit_of():
    k = phase35_prereg.FULL_FIDELITY_K
    assert phase39_prereg.unit_of([0] * (k - 1) + [1]) == 1
    assert phase39_prereg.unit_of([0] * k) == 0
    assert phase39_prereg.unit_of([True] + [False] * (k - 1)) == 1
    for hits in ([], [1], [0] * (k - 1), [0] * (k + 1)):
        with pytest.raises(SystemExit, match=r"^\[phase39_prereg\] .*D-07"):
            phase39_prereg.unit_of(hits)


def test_input_guards_refuse_zero_n_and_non_integer_counts():
    """IN-02: n = 0 and non-int (float, bool) counts and ranks are SystemExit, never arithmetic."""
    refused = (
        lambda: phase39_prereg.draw_rate(0, 0),
        lambda: phase39_prereg.draw_rate(1.0, 48),
        lambda: phase39_prereg.draw_rate(49, 48),
        lambda: phase39_prereg.count_status("damage", 0, 0, 0),
        lambda: phase39_prereg.count_status("collapse", 0, 0, 0),
        lambda: phase39_prereg.count_status("damage", 0.5, 1, 1),
        lambda: phase39_prereg.count_status("damage", 0, True, 1),
        lambda: phase39_prereg.count_status("damage", 0, 1, 1.0),
        lambda: phase39_prereg.damage_reachable(0, 0),
        lambda: phase39_prereg.rank_status(1.5, 1),
        lambda: phase39_prereg.rank_status(1, True),
        lambda: phase39_prereg.rank_of_mean_nll({"t": []}, "t", ()),
    )
    for call in refused:
        with pytest.raises(SystemExit, match=r"^\[phase39_prereg\]"):
            call()
    assert phase39_prereg._prove_count("x", 0) is None
    assert phase39_prereg._prove_count("x", 1, low=1) is None
    for value, low in ((-1, 0), (0, 1), (False, 0), (2.0, 0), ("2", 0)):
        with pytest.raises(SystemExit, match=r"^\[phase39_prereg\] x is "):
            phase39_prereg._prove_count("x", value, low=low)


def test_predicted_hit_rate():
    import math

    assert phase39_prereg.predicted_hit_rate(0.0) == 1.0
    assert phase39_prereg.predicted_hit_rate(math.log(2)) == 0.5
    assert phase39_prereg.predicted_hit_rate(3.0) == math.exp(-3.0)


def test_anchor_seed_index_is_slot_position_times_k():
    for i, slot in enumerate(_SLOT_ORDER):
        assert phase39_prereg.anchor_seed_index(slot) == i * phase35_prereg.FULL_FIDELITY_K
    with pytest.raises(SystemExit, match=r"^\[phase39_prereg\]"):
        phase39_prereg.anchor_seed_index("planted")


def test_anchor_seed_windows_coincide_with_a2_windows():
    """D-28, declared: the anchor's sampled draws use the A2 seed window of seed_index = the slot's
    position (draw_all passes ``seed_index * K`` as ``index``)."""
    import phase14_recall
    import phase18_extraction

    k = phase39_prereg.K
    assert phase18_extraction.K == k
    for i, slot in enumerate(_SLOT_ORDER):
        anchor = [
            phase14_recall.SEED + phase39_prereg.anchor_seed_index(slot) + j for j in range(k - 1)
        ]
        a2 = [phase14_recall.question_seed(i * phase18_extraction.K) + j for j in range(k - 1)]
        assert anchor == a2, slot


def test_e6_entries_follow_the_fill():
    import collections

    pairs = phase39_prereg.e6_entries()
    assert type(pairs) is tuple
    assert len(pairs) == len(phase39_prereg.E6_ENTRY_SUBSET) == 216
    assert tuple(i for i, _ in pairs) == phase39_prereg.E6_ENTRY_SUBSET
    entries = phase35_prereg.a2_corpus_entries()
    for i, entry in pairs:
        assert entry is entries[i] or entry == entries[i]
        assert entry["family"] == "A2"
    per_slot = collections.Counter(entry["slot"] for _, entry in pairs)
    assert per_slot == dict.fromkeys(_SLOT_ORDER, _N_QUESTIONS)


def test_minted_members_are_the_cleared_prefix():
    minting = _record(phase38_prereg.MINTING_RECORD)["slots"]
    taught = {slot: value for slot, value in zip(_SLOT_ORDER, _taught_values(), strict=True)}
    for slot in _SLOT_ORDER:
        members = phase39_prereg.minted_members(slot)
        assert len(members) == phase39_prereg.MINTED_SET_SIZE - 1 == 7, slot
        assert list(members) == minting[slot]["cleared"][:7], slot
        assert taught[slot] not in members, slot


def _taught_values():
    import phase14_factset

    by_slot = {f.slot: f.value for f in phase14_factset.LOCKED_FACTS}
    return [by_slot[slot] for slot in _SLOT_ORDER]


def test_suffix_premise_holds_for_every_entry():
    """D-23b: every A2 prompt is its guarded span plus the first realized_injection ids of the
    taught value, and every committed A2 draw (all eight records, adapter-on included) carries its
    entry's realized_injection."""
    import phase18_extraction

    from personacore.tokenizer.io import from_json

    tok = from_json(_ROOT / "artifacts" / "tokenizer.json")
    values = phase39_prereg._values()
    entries = phase35_prereg.a2_corpus_entries()
    held = [
        list(e["prompt_ids"])
        == phase18_extraction._guarded_span(e)
        + tok.encode(values[e["fact_id"]])[: e["realized_injection"]]
        for e in entries
    ]
    assert (sum(held), len(held)) == (216, 216)
    assert {e["realized_injection"] for e in entries} == {1, 2}
    by_key = {(e["fact_id"], e["tier"], e["seed_index"]): e["realized_injection"] for e in entries}
    assert len(by_key) == 216
    for reading, pin in phase39_prereg.A2_RECORDS.items():
        a2 = [d for d in _record(pin["path"])["draws"] if d["family"] == "A2"]
        carried = [
            by_key[(d["fact_id"], d["tier"], d["seed_index"])] == d["realized_injection"]
            for d in a2
        ]
        assert (sum(carried), len(carried)) == (216, 216), reading
        assert {(d["fact_id"], d["tier"], d["seed_index"]) for d in a2} == set(by_key), reading


# =================================================================================================
# (9) PLAN 39-02 TASK 2: STATUSES, THE PER-CELL CLASSIFIER, CLASS COUNTS AND RANK SUMMARIES — the
# full truth table and the committed-data oracle.
# =================================================================================================

_INTACT, _LOST, _UNREACH, _ALREADY = "INTACT", "LOST", "UNREACHABLE_AT_SIZE", "ALREADY_AT_K0"


def test_lost_rank_status():
    assert phase39_prereg.rank_status(1, 1) == _INTACT
    assert phase39_prereg.rank_status(2, 1) == _LOST
    assert phase39_prereg.rank_status(1, 2) == _ALREADY
    assert phase39_prereg.rank_status(3, 2) == _ALREADY
    for bad in ((0, 1), (1, 0)):
        with pytest.raises(SystemExit, match=r"^\[phase39_prereg\]"):
            phase39_prereg.rank_status(*bad)


def test_lost_count_status_collapse():
    status = phase39_prereg.count_status
    assert status("collapse", 0, 5, 27) == _LOST
    assert status("collapse", 3, 5, 27) == _INTACT
    assert status("collapse", 0, 0, 27) == _ALREADY
    assert status("collapse", 4, 0, 27) == _ALREADY
    assert status("collapse", 0, 1, 1) == _LOST
    assert status("collapse", 1, 0, 1) == _ALREADY
    for bad in (("planted", 0, 5, 27), ("collapse", 28, 5, 27), ("collapse", 0, -1, 27)):
        with pytest.raises(SystemExit, match=r"^\[phase39_prereg\]"):
            status(*bad)


def test_lost_count_status_damage():
    status = phase39_prereg.count_status
    # person_name k8: the drop equals MARGIN exactly; strict > leaves it intact.
    assert 26 / 27 - 18 / 27 == phase38_prereg.MARGIN
    assert status("damage", 18, 26, 27) == _INTACT
    # D-33: (21 - 13) / 27 == MARGIN, but the committed formula 21/27 - 13/27 is above it.
    assert (21 - 13) / 27 == phase38_prereg.MARGIN < 21 / 27 - 13 / 27
    assert status("damage", 13, 21, 27) == _LOST
    assert status("damage", 17, 26, 27) == _LOST
    assert status("damage", 0, 8, 27) == _UNREACH
    assert status("damage", 0, 9, 27) == _LOST
    assert status("damage", 0, 1, 1) == _LOST
    assert status("damage", 1, 1, 1) == _INTACT
    assert status("damage", 0, 0, 1) == _UNREACH


def test_lost_count_status_damage_on_every_exact_eight_drop():
    got = {c: phase39_prereg.count_status("damage", c - 8, c, 27) for c in range(8, 28)}
    assert len(got) == 20
    assert {c for c, s in got.items() if s == _LOST} == {15, 17, 19, 21}
    assert {c for c, s in got.items() if s == _UNREACH} == {8}
    assert sum(s == _INTACT for s in got.values()) == 15


def test_reachability_threshold_is_derived():
    reachable = [c for c in range(28) if phase39_prereg.damage_reachable(c, 27)]
    assert reachable == list(range(9, 28))
    assert phase39_prereg.damage_reachable(1, 1) is True
    assert phase39_prereg.damage_reachable(0, 1) is False
    with pytest.raises(SystemExit, match=r"^\[phase39_prereg\]"):
        phase39_prereg.damage_reachable(28, 27)


def _cell(r_a, r_q, g_a, g_q):
    return phase39_prereg._precedence({"R_a": r_a, "R_q": r_q, "G_a": g_a, "G_q": g_q})


def test_classify_cell_sufficiency_table():
    table = {
        (_LOST, _INTACT): "CONTEXT_SUFFICIENT",
        (_INTACT, _LOST): "INSTRUMENT_SUFFICIENT",
        (_LOST, _LOST): "EITHER",
        (_INTACT, _INTACT): "INTERACTION_ONLY",
    }
    for (r_q, g_a), name in table.items():
        assert _cell(_INTACT, r_q, g_a, _LOST) == {"class": name, "disagreement": True}


def test_classify_cell_no_disagreement_and_reverse_disagreement():
    """Ruling e: NO_DISAGREEMENT only when R_a and G_q agree; R_a LOST with G_q INTACT is the named
    REVERSE_DISAGREEMENT, outside every sufficiency class."""
    expected = {
        (_LOST, _LOST): "NO_DISAGREEMENT",
        (_INTACT, _INTACT): "NO_DISAGREEMENT",
        (_LOST, _INTACT): "REVERSE_DISAGREEMENT",
    }
    for (r_a, g_q), name in expected.items():
        assert phase39_prereg.disagreement_of(r_a, g_q) == {"class": name, "disagreement": False}
        for r_q in phase39_prereg.STATUSES:
            for g_a in phase39_prereg.STATUSES:
                assert _cell(r_a, r_q, g_a, g_q) == {"class": name, "disagreement": False}
    assert phase39_prereg.disagreement_of(_INTACT, _LOST) == {"class": None, "disagreement": True}
    assert phase39_prereg.disagreement_of(_LOST, _UNREACH) == {
        "class": _UNREACH,
        "disagreement": None,
    }
    assert phase39_prereg.disagreement_of(_ALREADY, _INTACT) == {
        "class": _ALREADY,
        "disagreement": None,
    }
    assert phase39_prereg.REVERSE_DISAGREEMENT not in phase39_prereg.CLASSES
    assert phase39_prereg.OUTCOMES == phase39_prereg.CLASSES + (
        "REVERSE_DISAGREEMENT",
        _UNREACH,
        _ALREADY,
    )
    with pytest.raises(SystemExit, match=r"^\[phase39_prereg\]"):
        phase39_prereg.disagreement_of("planted", _LOST)


def test_classify_cell_wr01_precedence():
    assert _cell(_ALREADY, _LOST, _LOST, _LOST) == {"class": _ALREADY, "disagreement": None}
    assert _cell(_ALREADY, _INTACT, _INTACT, _UNREACH) == {"class": _UNREACH, "disagreement": None}
    assert _cell(_INTACT, _INTACT, _INTACT, _UNREACH) == {"class": _UNREACH, "disagreement": None}
    assert _cell(_LOST, _INTACT, _INTACT, _ALREADY) == {"class": _ALREADY, "disagreement": None}
    assert _cell(_INTACT, _LOST, _UNREACH, _LOST) == {"class": _UNREACH, "disagreement": True}
    assert _cell(_INTACT, _ALREADY, _UNREACH, _LOST) == {"class": _UNREACH, "disagreement": True}
    assert _cell(_INTACT, _ALREADY, _INTACT, _LOST) == {"class": _ALREADY, "disagreement": True}


def test_classify_wr01_helper_orders_unreachable_first():
    assert phase39_prereg._wr01(_ALREADY, _UNREACH) == _UNREACH
    assert phase39_prereg._wr01(_INTACT, _ALREADY) == _ALREADY
    assert phase39_prereg._wr01(_INTACT, _LOST) is None


def test_classify_cell_exhaustive():
    import itertools

    sufficiency = set(phase39_prereg.CLASSES[:4])
    names = set(phase39_prereg.OUTCOMES)
    seen = set()
    combos = list(itertools.product(phase39_prereg.STATUSES, repeat=4))
    assert len(combos) == 256
    for r_a, r_q, g_a, g_q in combos:
        out = _cell(r_a, r_q, g_a, g_q)
        assert set(out) == {"class", "disagreement"}
        assert out["class"] in names
        seen.add(out["class"])
        decided = r_a in (_INTACT, _LOST) and g_q in (_INTACT, _LOST)
        disagree = r_a == _INTACT and g_q == _LOST
        assert out["disagreement"] == (disagree if decided else None)
        if out["class"] in sufficiency:
            assert disagree and r_q in (_INTACT, _LOST) and g_a in (_INTACT, _LOST)
        if decided and not disagree:
            reverse = (r_a, g_q) == (_LOST, _INTACT)
            assert out["class"] == ("REVERSE_DISAGREEMENT" if reverse else "NO_DISAGREEMENT")
    assert seen == names
    for bad in (
        {"R_a": _INTACT, "R_q": _INTACT, "G_a": _INTACT},
        {"R_a": _INTACT, "R_q": _INTACT, "G_a": _INTACT, "G_q": _LOST, "X": _LOST},
        {"R_a": "planted", "R_q": _INTACT, "G_a": _INTACT, "G_q": _LOST},
    ):
        with pytest.raises(SystemExit, match=r"^\[phase39_prereg\]"):
            phase39_prereg._precedence(bad)


def _door_cell(event, reading, slot, statuses):
    return {**phase39_prereg.cell_spec(event, reading, slot), **_cell(*statuses)}


def test_class_counts_publish_denominators():
    rows = [
        ("k8", "person_name", (_INTACT, _LOST, _INTACT, _LOST)),
        ("k8", "pet_name", (_INTACT, _LOST, _INTACT, _LOST)),
        ("k16", "person_name", (_INTACT, _INTACT, _LOST, _LOST)),
        ("k16", "pet_name", (_INTACT, _INTACT, _UNREACH, _LOST)),
        ("k32", "person_name", (_LOST, _LOST, _LOST, _LOST)),
        ("k32", "pet_name", (_ALREADY, _LOST, _LOST, _LOST)),
        ("M2", "person_name", (_LOST, _LOST, _LOST, _INTACT)),
        ("M2", "pet_name", (_INTACT, _INTACT, _INTACT, _UNREACH)),
        ("M2", "cat_name", (_INTACT, _LOST, _LOST, _LOST)),
    ]
    cells = [_door_cell("damage", reading, slot, st) for reading, slot, st in rows]
    counts = phase39_prereg.class_counts(cells)
    json.dumps(counts)
    assert set(counts) == {"event", "combined", "prefixes", "M2", "m2_label"}
    assert counts["event"] == "damage"
    assert "another training" in counts["m2_label"] and "k0" in counts["m2_label"]
    combined = counts["combined"]
    assert combined["cells"] == 9
    assert combined["disagreement_cells"] == 5
    assert combined["reverse_disagreement_cells"] == 1
    assert combined["denominator"] == "disagreement_cells"
    # IN-01: the step-1 cells (disagreement None) apart from the step-3 WR-01 outcome.
    assert combined["undecided_cells"] == 2
    assert combined["undecided_by_class"] == {_UNREACH: 1, _ALREADY: 1}
    assert combined["by_class"] == {
        "CONTEXT_SUFFICIENT": 2,
        "INSTRUMENT_SUFFICIENT": 1,
        "EITHER": 1,
        "INTERACTION_ONLY": 0,
        "NO_DISAGREEMENT": 1,
        "REVERSE_DISAGREEMENT": 1,
        _UNREACH: 2,
        _ALREADY: 1,
    }
    assert combined["disagreement_by_class"] == {
        "CONTEXT_SUFFICIENT": 2,
        "INSTRUMENT_SUFFICIENT": 1,
        "EITHER": 1,
        "INTERACTION_ONLY": 0,
        _UNREACH: 1,
        _ALREADY: 0,
    }
    assert combined["shares"] == {
        "CONTEXT_SUFFICIENT": 2 / 5,
        "INSTRUMENT_SUFFICIENT": 1 / 5,
        "EITHER": 1 / 5,
        "INTERACTION_ONLY": 0.0,
        _UNREACH: 1 / 5,
        _ALREADY: 0.0,
    }
    # Ruling g: M2 apart from the prefix readings; the two partition the combined.
    prefixes, m2 = counts["prefixes"], counts["M2"]
    assert (prefixes["cells"], m2["cells"]) == (6, 3)
    assert (prefixes["disagreement_cells"], m2["disagreement_cells"]) == (4, 1)
    assert m2["reverse_disagreement_cells"] == 1 and m2["undecided_by_class"][_UNREACH] == 1
    assert m2["by_class"]["EITHER"] == 1 and prefixes["by_class"]["EITHER"] == 0
    for key in ("by_class", "undecided_by_class", "disagreement_by_class"):
        for name, count in combined[key].items():
            assert prefixes[key][name] + m2[key][name] == count, (key, name)
    assert phase39_prereg._tally([])["cells"] == 0
    none = phase39_prereg._tally([_door_cell("damage", "k8", "person_name", (_LOST,) * 4)])
    assert none["disagreement_cells"] == 0
    assert set(none["shares"].values()) == {None}


def test_class_counts_refuses_mixed_events_and_cells_outside_the_door():
    good = _door_cell("damage", "k8", "person_name", (_INTACT, _LOST, _INTACT, _LOST))
    for bad in (
        [],
        [good, _door_cell("collapse", "k8", "pet_name", (_INTACT, _LOST, _INTACT, _LOST))],
        [good, good],
        [{**good, "reading": "k0"}],
        [{**good, "class": "planted"}],
    ):
        with pytest.raises(SystemExit, match=r"^\[phase39_prereg\]"):
            phase39_prereg.class_counts(bad)


# Measured at plan time (39-02-PLAN interfaces): the published disagreement, R_a INTACT and G_q
# LOST, on the committed ranks and counts. 39-RESEARCH M9's "12 collapse cells" does not reproduce:
# pet_name at k78 and M2 has R_a rank 2 (LOST), so the measured 9 is pinned here.
_DAMAGE_CELLS = {
    ("k8", "hometown"),
    ("k16", "person_name"),
    ("k16", "pet_name"),
    ("k16", "hometown"),
    ("k32", "person_name"),
    ("k32", "pet_name"),
    ("k32", "sibling_name"),
    ("k32", "hometown"),
    ("k32", "street"),
    ("k32", "house_number"),
    ("k64", "person_name"),
    ("k64", "pet_name"),
    ("k64", "cat_name"),
    ("k64", "sibling_name"),
    ("k64", "hometown"),
    ("k64", "street"),
    ("k64", "house_number"),
    ("k78", "person_name"),
    ("k78", "cat_name"),
    ("k78", "sibling_name"),
    ("k78", "hometown"),
    ("k78", "street"),
    ("k78", "birth_year"),
    ("k78", "house_number"),
}
_COLLAPSE_CELLS = {
    ("k64", "person_name"),
    ("k64", "pet_name"),
    ("k64", "sibling_name"),
    ("k64", "hometown"),
    ("k64", "street"),
    ("k78", "person_name"),
    ("k78", "sibling_name"),
    ("k78", "hometown"),
    ("k78", "street"),
}


def _committed_values(cell):
    """(values, k0) of the two committed readings, R_a and G_q, for a door cell."""
    ranks = phase38_prereg.committed_gate_ranks()
    counts = phase39_prereg.committed_a2_counts()
    reading, slot, ref = cell["reading"], cell["slot"], cell["reference"]
    return (
        {"R_a": ranks[reading][slot]["rank"], "G_q": counts[reading][slot]},
        {"R_a": ranks[ref][slot]["rank"], "G_q": counts[ref][slot]},
    )


def test_classify_committed_disagreement_oracle():
    published = {}
    for event in phase39_prereg.EVENTS:
        cells = set()
        for cell in phase39_prereg.cells(event):
            statuses = phase39_prereg.cell_statuses(cell, *_committed_values(cell))
            assert statuses["G_q"] in (_INTACT, _LOST), cell
            if statuses == {"R_a": _INTACT, "G_q": _LOST}:
                cells.add((cell["reading"], cell["slot"]))
        published[event] = cells
    counts = phase39_prereg.committed_a2_counts()
    ref = phase39_prereg.REFERENCE_READING
    assert min(counts[ref].values()) >= 18
    assert published["damage"] == _DAMAGE_CELLS and len(_DAMAGE_CELLS) == 24
    assert published["collapse"] == _COLLAPSE_CELLS and len(_COLLAPSE_CELLS) == 9
    assert not [c for c in published["damage"] | published["collapse"] if c[0] == "M2"]


def test_cell_door_is_cell_readings_by_slots_for_both_events():
    """WR-02 / ruling f: 48 cells per event; k0 and adapter-off are never cells."""
    for event in phase39_prereg.EVENTS:
        door = phase39_prereg.cells(event)
        assert len(door) == len(phase39_prereg.CELL_READINGS) * len(_SLOT_ORDER) == 48
        assert [(c["reading"], c["slot"]) for c in door] == [
            (r, s) for r in phase39_prereg.CELL_READINGS for s in _SLOT_ORDER
        ]
        for cell in door:
            json.dumps(cell)
            assert cell["event"] == event and cell["reference"] == "k0"
            assert cell["n"] == {"R_q": 27, "G_a": 1, "G_q": 27}
            assert phase39_prereg.cell_spec(event, cell["reading"], cell["slot"]) == cell
    for event, reading, slot in (
        ("damage", "k0", "pet_name"),
        ("collapse", "k0", "pet_name"),
        ("collapse", "adapter_off", "person_name"),
        ("damage", "adapter_off", "person_name"),
        ("damage", "k99", "person_name"),
        ("damage", "k8", "planted"),
        ("planted", "k8", "person_name"),
    ):
        with pytest.raises(SystemExit, match=r"^\[phase39_prereg\]"):
            phase39_prereg.cell_spec(event, reading, slot)


def test_cell_statuses_and_classify_refuse_a_cell_outside_the_door():
    good = phase39_prereg.cell_spec("damage", "k8", "person_name")
    values = {"R_a": 1, "R_q": 27, "G_a": 1, "G_q": 18}
    k0 = {"R_a": 1, "R_q": 27, "G_a": 1, "G_q": 26}
    assert phase39_prereg._door(good) is None
    for bad in (
        {**good, "reading": "k0"},
        {**good, "reading": "adapter_off"},
        {**good, "n": {"R_q": 26, "G_a": 1, "G_q": 26}},
        {**good, "reference": "k8"},
        {k: v for k, v in good.items() if k != "n"},
        [good],
    ):
        with pytest.raises(SystemExit, match=r"^\[phase39_prereg\]"):
            phase39_prereg._door(bad)
        with pytest.raises(SystemExit, match=r"^\[phase39_prereg\]"):
            phase39_prereg.cell_statuses(bad, values, k0)
        with pytest.raises(SystemExit, match=r"^\[phase39_prereg\]"):
            phase39_prereg.classify_cell(bad, values, k0)


def test_cell_statuses_use_the_door_n():
    damage = phase39_prereg.cell_spec("damage", "k8", "person_name")
    collapse = phase39_prereg.cell_spec("collapse", "k8", "person_name")
    k0 = {"R_a": 1, "R_q": 26, "G_a": 1, "G_q": 26}
    values = {"R_a": 2, "R_q": 17, "G_a": 0, "G_q": 18}
    assert phase39_prereg.cell_statuses(damage, values, k0) == {
        "R_a": _LOST,
        "R_q": _LOST,
        "G_a": _LOST,
        "G_q": _INTACT,
    }
    assert phase39_prereg.cell_statuses(collapse, values, k0) == {
        "R_a": _LOST,
        "R_q": _INTACT,
        "G_a": _LOST,
        "G_q": _INTACT,
    }
    assert phase39_prereg.cell_statuses(damage, {"G_q": 0}, {"G_q": 8}) == {"G_q": _UNREACH}
    assert phase39_prereg._status("damage", "G_a", 0, 1) == _LOST
    assert phase39_prereg._status("collapse", "R_a", 1, 2) == _ALREADY
    assert phase39_prereg._paired({"G_q": 1, "R_a": 1}, {"R_a": 1, "G_q": 1}) == ("R_a", "G_q")
    for bad_values, bad_k0 in (({}, {}), ({"G_q": 1}, {"R_a": 1}), ({"X": 1}, {"X": 1})):
        with pytest.raises(SystemExit, match=r"^\[phase39_prereg\]"):
            phase39_prereg._paired(bad_values, bad_k0)
    with pytest.raises(SystemExit, match=r"^\[phase39_prereg\]"):
        phase39_prereg._paired([1], {"G_q": 1})


def test_classify_cell_through_the_door():
    cell = phase39_prereg.cell_spec("damage", "k32", "pet_name")
    values = {"R_a": 1, "R_q": 10, "G_a": 1, "G_q": 2}
    k0 = {"R_a": 1, "R_q": 27, "G_a": 1, "G_q": 27}
    out = phase39_prereg.classify_cell(cell, values, k0)
    json.dumps(out)
    assert out == {
        **cell,
        "values": values,
        "k0": k0,
        "statuses": {"R_a": _INTACT, "R_q": _LOST, "G_a": _INTACT, "G_q": _LOST},
        "class": "CONTEXT_SUFFICIENT",
        "disagreement": True,
    }
    with pytest.raises(SystemExit, match=r"^\[phase39_prereg\] a cell is classified on all"):
        phase39_prereg.classify_cell(cell, {"R_a": 1, "G_q": 2}, {"R_a": 1, "G_q": 27})


def test_baseline_table_is_the_k0_statuses_per_slot():
    """Ruling f: the k0 statuses come out as a baseline table, never as cells."""
    k0 = dict.fromkeys(_SLOT_ORDER, {"R_a": 1, "R_q": 27, "G_a": 1, "G_q": 27})
    k0["person_name"] = {"R_a": 2, "R_q": 0, "G_a": 0, "G_q": 8}
    table = phase39_prereg.baseline_table(k0)
    json.dumps(table)
    assert tuple(table) == _SLOT_ORDER
    assert table["person_name"] == {
        "R_a": {"value": 2, "collapse": _ALREADY, "damage": _ALREADY},
        "R_q": {"value": 0, "collapse": _ALREADY, "damage": _UNREACH},
        "G_a": {"value": 0, "collapse": _ALREADY, "damage": _UNREACH},
        "G_q": {"value": 8, "collapse": _INTACT, "damage": _UNREACH},
    }
    assert table["pet_name"]["G_q"] == {"value": 27, "collapse": _INTACT, "damage": _INTACT}
    committed = phase39_prereg.committed_a2_counts()["k0"]
    ranks = phase38_prereg.committed_gate_ranks()["k0"]
    partial = {s: {"R_a": ranks[s]["rank"], "G_q": committed[s]} for s in _SLOT_ORDER}
    assert {
        (key, row[key]["collapse"], row[key]["damage"])
        for row in phase39_prereg.baseline_table(partial).values()
        for key in row
    } == {("R_a", _INTACT, _INTACT), ("G_q", _INTACT, _INTACT)}
    with pytest.raises(SystemExit, match=r"^\[phase39_prereg\]"):
        phase39_prereg.baseline_table({"person_name": k0["person_name"]})


def _json_round_trip(blob):
    """What a record written by atomic_write_json (sort_keys=True) reads back as."""
    return json.loads(json.dumps(blob, sort_keys=True))


def test_door_outputs_survive_a_sorted_keys_json_round_trip():
    """Rafael 2026-10-05: no door check depends on key order, so cells, statuses and the baseline
    read back from a sort_keys record give exactly the results they gave before the write."""
    counts = phase39_prereg.committed_a2_counts()
    ranks = phase38_prereg.committed_gate_ranks()

    def four(reading, slot):
        # R_a and G_q committed; R_q and G_a test-built from G_q (not measured until E6 runs).
        g_q = counts[reading][slot]
        return {"R_a": ranks[reading][slot]["rank"], "R_q": g_q, "G_a": int(g_q > 0), "G_q": g_q}

    k0 = {slot: four(phase39_prereg.REFERENCE_READING, slot) for slot in _SLOT_ORDER}
    for event in phase39_prereg.EVENTS:
        classified = [
            phase39_prereg.classify_cell(
                cell, four(cell["reading"], cell["slot"]), k0[cell["slot"]]
            )
            for cell in phase39_prereg.cells(event)
        ]
        read_back = _json_round_trip(classified)
        assert [list(c) for c in read_back] != [list(c) for c in classified]  # keys reordered
        assert read_back == classified
        assert phase39_prereg.class_counts(read_back) == phase39_prereg.class_counts(classified)
        if event == phase39_prereg.EVENTS[1]:
            assert phase39_prereg.tie_audit(read_back) == phase39_prereg.tie_audit(classified)
        for cell, again in zip(phase39_prereg.cells(event), read_back):
            door = _json_round_trip({field: again[field] for field in cell})
            assert list(door) != list(cell)  # the door cell itself comes back reordered
            assert phase39_prereg.classify_cell(
                door, again["values"], again["k0"]
            ) == phase39_prereg.classify_cell(cell, again["values"], again["k0"])
    k0_back = _json_round_trip(k0)
    assert tuple(k0_back) != _SLOT_ORDER  # sorted slot names, not the project order
    table = phase39_prereg.baseline_table(k0_back)
    assert table == phase39_prereg.baseline_table(k0)
    assert tuple(table) == _SLOT_ORDER  # output keeps the project's order


def test_drop_audit_names_the_rounding_decided_ties():
    """WR-03 / ruling j: status by both formulas; the four n = 27 flips and (26, 18)."""
    for count_k0 in (15, 17, 19, 21):
        audit = phase39_prereg.drop_audit(count_k0 - 8, count_k0, 27)
        assert audit["count_drop"] == phase38_prereg.MARGIN < audit["rate_drop"], count_k0
        assert (audit["status_committed"], audit["status_exact"]) == (_LOST, _INTACT)
        assert audit["flip"] is True and audit["differs"] is True
    tie = phase39_prereg.drop_audit(18, 26, 27)
    assert tie["exact_margin_tie"] is True and tie["flip"] is False
    assert (tie["status_committed"], tie["status_exact"]) == (_INTACT, _INTACT)
    flips = [c for c in range(8, 28) if phase39_prereg.drop_audit(c - 8, c, 27)["flip"]]
    assert flips == [15, 17, 19, 21]
    assert phase39_prereg.drop_audit(0, 8, 27)["status_exact"] == _UNREACH
    unit = phase39_prereg.drop_audit(0, 1, 1)
    assert (unit["status_committed"], unit["status_exact"], unit["flip"]) == (_LOST, _LOST, False)
    assert phase39_prereg.drop_audit(0, 0, 1)["status_exact"] == _UNREACH
    # The prefix cells agree with Phase 38's audit field by field on the committed G_q counts.
    a2 = phase38_prereg.a2_counts()
    for cell in phase38_prereg.drop_formula_audit(a2)["cells"]:
        counts = a2[cell["slot"]]["counts"]
        mine = phase39_prereg.drop_audit(counts[cell["k"]], counts[0], 27)
        for field in ("rate_drop", "count_drop", "differs", "flip", "exact_margin_tie"):
            assert mine[field] == cell[field], (cell["slot"], cell["k"], field)


def _classified(reading, slot, values, k0, event="damage"):
    cell = phase39_prereg.cell_spec(event, reading, slot)
    return phase39_prereg.classify_cell(cell, values, k0)


def test_tie_audit_gives_the_class_by_both_formulas():
    k0 = {"R_a": 1, "R_q": 26, "G_a": 1, "G_q": 21}
    flipped = _classified("k8", "person_name", {"R_a": 1, "R_q": 26, "G_a": 1, "G_q": 13}, k0)
    assert flipped["class"] == "INTERACTION_ONLY"
    tied = _classified("M2", "pet_name", {"R_a": 1, "R_q": 18, "G_a": 0, "G_q": 21}, k0)
    assert tied["class"] == "NO_DISAGREEMENT"
    audit = phase39_prereg.tie_audit([flipped, tied])
    json.dumps(audit)
    assert audit["criterion"] is False and audit["margin"] == phase38_prereg.MARGIN
    assert audit["flips"] == [["k8", "person_name", "G_q"]]
    assert audit["exact_ties"] == [["M2", "pet_name", "R_q"]]
    assert audit["class_changes"] == [["k8", "person_name"]]
    first, second = audit["cells"]
    assert (first["class_committed"], first["class_exact"]) == (
        "INTERACTION_ONLY",
        "NO_DISAGREEMENT",
    )
    assert (second["class_committed"], second["class_exact"]) == ("NO_DISAGREEMENT",) * 2
    assert second["audits"]["G_a"]["n"] == 1 and second["audits"]["G_a"]["status_exact"] == _LOST
    assert set(first["audits"]) == {"R_q", "G_a", "G_q"}
    assert phase39_prereg.tie_audit([])["cells"] == []
    collapse = _classified("k8", "person_name", flipped["values"], k0, event="collapse")
    for bad in ([collapse], [{**flipped, "class": "EITHER"}], [{**flipped, "reading": "k0"}]):
        with pytest.raises(SystemExit, match=r"^\[phase39_prereg\]"):
            phase39_prereg.tie_audit(bad)


def test_rank_summaries():
    import math
    import random

    assert phase39_prereg.n1([1, 2, 1]) == 2
    assert phase39_prereg.median_rank([3, 1, 2]) == 2
    with pytest.raises(SystemExit, match=r"^\[phase39_prereg\]"):
        phase39_prereg.median_rank([1, 2])
    rng = random.Random(1337)
    for _ in range(300):
        ranks = [rng.choice((1, 1, 2, 3, 8)) for _ in range(_N_QUESTIONS)]
        assert (phase39_prereg.median_rank(ranks) == 1) == (phase39_prereg.n1(ranks) >= 14)
    nll = {"taught": [1.0, 3.0], "a": [2.5, 2.4], "b": [0.5, 3.0]}
    means = {c: math.fsum(v) / len(v) for c, v in nll.items()}
    want = phase38_prereg.rank_in_prefix(means, "taught", ("a", "b"))
    assert phase39_prereg.rank_of_mean_nll(nll, "taught", ("a", "b")) == want == 2
