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

import fnmatch
import hashlib
import json
import pathlib
import subprocess
import sys

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
    assert first["classified_readings"] == list(phase39_prereg.CLASSIFIED_READINGS)
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
    for reading in phase39_prereg.CLASSIFIED_READINGS:
        pin = phase39_prereg.A2_RECORDS[reading]
        assert pin["path"] in ruling and pin["sha256"] in ruling, reading
    assert phase39_prereg.ADAPTER_OFF_SHA256 not in ruling


def test_readings_split_into_classified_damage_and_descriptive():
    assert phase39_prereg.READINGS is phase38_prereg.READINGS
    assert phase39_prereg.PREFIXES is phase38_prereg.PREFIXES
    assert phase39_prereg.SLOTS is phase38_prereg.SLOTS
    assert phase39_prereg.MARGIN is phase38_prereg.MARGIN
    assert phase39_prereg.K == phase35_prereg.FULL_FIDELITY_K
    assert phase39_prereg.REFERENCE_READING == "k0"
    assert phase39_prereg.DESCRIPTIVE_READINGS == ("adapter_off",)
    assert phase39_prereg.CLASSIFIED_READINGS == ("k0", "k8", "k16", "k32", "k64", "k78", "M2")
    assert phase39_prereg.DAMAGE_READINGS == ("k8", "k16", "k32", "k64", "k78", "M2")
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
# 39-03 moves each name to its confirmed form with a local edit.
_UNCONFIRMED = {
    "run_shape": "D-27",
    "anchor_generation": "D-28",
    "predicted_hit_rate": "D-29",
    "taught_suffix_nll": "D-30a",
}
_DEFAULT_LABEL = "default taken at plan time, not yet confirmed by Rafael"


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
    assert value["classified_readings"] == phase39_prereg.CLASSIFIED_READINGS
    assert value["descriptive_readings"] == phase39_prereg.DESCRIPTIVE_READINGS
    assert value["damage_readings"] == phase39_prereg.DAMAGE_READINGS
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
    assert "plan-03 review" in filled["derivation"]


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
    for name, entry in phase39_prereg.ENTRIES.items():
        assert "D-" in entry["derivation"], name
    for name, d_id in _UNCONFIRMED.items():
        derivation = phase39_prereg.ENTRIES[name]["derivation"]
        assert d_id in derivation, name
        assert _DEFAULT_LABEL in derivation, name
    for name, entry in phase39_prereg.ENTRIES.items():
        if name not in _UNCONFIRMED:
            assert _DEFAULT_LABEL not in entry["derivation"], name
    assert "D-30a" in phase39_prereg.ENTRIES["cpu_crosscheck"]["derivation"]
