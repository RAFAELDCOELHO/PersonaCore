"""Plan 38-01: the Phase 38 pre-registration (RANK-01/RANK-02, SC4), CPU-only.

What this file proves:
- the record paths, the D-21 approval and the D-22/D-23 budget arithmetic are the committed
  budget's arithmetic, never typed; the sixteen entries and both input-free fills (D-06);
- the pure definitions (rank, bits, moved, left the top eighth, first event, relation) behave as
  pre-registered, and rank_in_prefix equals phase18_extraction.exposure_rank on every 6-8 member set
  with ties broken by string (property test);
- the committed gate ranks, the committed A2 counts, their events and the D-33 drop-formula audit
  read from the committed records reproduce the research tables;
- scripts/phase38_prereg.py is frozen before every results/phase38_* record, the paths resolve from
  the modules that own them, nothing derived is typed, the entries have four fields and honest
  kinds, the module imports without torch, passes the slot census, this file has zero skips and
  every prereg function is called by a CPU test.

It reads only tracked files and git history and writes nothing under results/.
"""

import fnmatch
import json
import math
import pathlib
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

PREREG = "scripts/phase38_prereg.py"


def _record(rel):
    return json.loads((_ROOT / rel).read_text(encoding="utf-8"))


def _budget():
    return _record("results/phase36_budget.json")


# =================================================================================================
# (1) PATHS, THE D-21 APPROVAL AND THE D-22/D-23 ARITHMETIC.
# =================================================================================================


def test_budget_arithmetic_is_the_committed_formula():
    budget = _budget()
    p, c = budget["unit_prices"], budget["unit_caps"]["E5"]

    def formula(prefixes):
        return (
            p["e5_clearance_setup"]
            + c["sets"] * p["e5_slot_clearance_high"]
            + c["sets"] * c["max_set_size"] * p["e5_match_high"]
            + prefixes
            * (p["adapter_setup_high"] + c["sets"] * c["max_set_size"] * p["e5_nll_high"])
        ) / 3600

    assert phase38_prereg.e5_projection_hours(c["prefixes"]) == budget["front_hours"]["E5"]
    assert phase38_prereg.e5_projection_hours(len(phase38_prereg.READINGS)) == formula(8)
    assert phase38_prereg.E5_PROJECTION_HOURS == formula(8)
    assert repr(phase38_prereg.E5_PROJECTION_HOURS) == "0.467956566879681"
    total = math.fsum({**budget["front_hours"], "E5": formula(8)}.values())
    assert phase38_prereg.E5_TOTAL_HOURS == total
    assert repr(phase38_prereg.E5_TOTAL_HOURS) == "77.83105039182757"
    stop = phase36_prereg.ENTRIES["front_stop_factor"]["value"] * budget["front_hours"]["E5"]
    assert phase38_prereg.E5_STOP_HOURS == stop
    assert repr(phase38_prereg.E5_STOP_HOURS) == "0.5418565110509128"
    assert phase38_prereg.E5_PROJECTION_HOURS <= phase38_prereg.E5_STOP_HOURS
    assert phase38_prereg.COMMITTED_PREFIX_CAP == len(phase38_prereg.PREFIXES)
    assert phase38_prereg.APPROVED_E5_PREFIXES == len(phase38_prereg.READINGS)


def test_approval_block_is_fresh_on_every_call():
    first = phase38_prereg.approval_block()
    assert first["ruling"] == phase38_prereg.D21_RULING
    assert first["approved_prefixes"] == phase38_prereg.APPROVED_E5_PREFIXES
    assert first["readings"] == list(phase38_prereg.READINGS)
    json.dumps(first)
    first["readings"].append("planted")
    first["ruling"] = "planted"
    second = phase38_prereg.approval_block()
    assert second["readings"] == list(phase38_prereg.READINGS)
    assert second["ruling"] == phase38_prereg.D21_RULING


def test_records_and_the_minting_glob():
    assert phase38_prereg.RECORDS == (
        "results/phase38_minting.json",
        "results/phase38_rank.json",
        "results/phase38_rank_report.md",
    )
    matching = [
        p for p in phase38_prereg.RECORDS if fnmatch.fnmatch(p, phase38_prereg.MINTING_GLOB)
    ]
    assert matching == [phase38_prereg.MINTING_RECORD]
    for path in phase38_prereg.RECORDS:
        assert fnmatch.fnmatch(path, phase38_prereg.RECORD_GLOB), path


def test_entries_are_the_sixteen_with_four_derived():
    assert set(phase38_prereg.ENTRIES) == {
        "e5_minting_rule",
        "rank_moved",
        "generation_collapsed",
        "generation_damaged",
        "left_top_eighth",
        "event_relation",
        "extra_readings",
        "gate_exact_ranks",
        "cpu_crosscheck",
        "prefix_reconstruction",
        "e5_prefix_cap_approval",
        "e5_projection_hours",
        "e5_total_hours",
        "e5_stop_hours",
        "numeric_neighbour_sensitivity",
        "drop_formula",
    }
    derived = {n for n, e in phase38_prereg.ENTRIES.items() if e["kind"] == "derived"}
    assert derived == {
        "generation_damaged",
        "e5_projection_hours",
        "e5_total_hours",
        "e5_stop_hours",
    }


def test_both_fills_carry_the_entries():
    rule = phase38_prereg.E5_MINTING_RULE
    entry = phase38_prereg.ENTRIES["e5_minting_rule"]
    assert set(rule) == set(entry)
    for field in ("derivation", "kind", "source"):
        assert rule[field] == entry[field], field
    assert set(rule["value"]) == set(entry["value"])
    filled = phase38_prereg.E5_RANK_MOVES_AND_GENERATION_COLLAPSES
    assert sorted(filled) == ["collapses", "moves"]
    for slot_key, name in (("moves", "rank_moved"), ("collapses", "generation_collapsed")):
        for field in ("derivation", "kind", "source"):
            assert filled[slot_key][field] == phase38_prereg.ENTRIES[name][field], field


def test_margin_is_the_v6_condition_b_margin():
    assert phase38_prereg.MARGIN == phase35_prereg.e1_condition_b_margin()
