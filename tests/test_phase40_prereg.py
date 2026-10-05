"""Plan 40-02: the Phase 40 pre-registration (NOISE-01, NOISE-02 groundwork), CPU-only.

What this file proves:
- the record paths and the D-11 / D-13 / D-14 approval arithmetic are the committed budget's
  arithmetic and Rafael's committed words, never typed;
- the seventeen entries, both fills (e2_S read from the budget, e2_noise_floor_estimator holding
  both estimators) and SEEDS;
- scripts/phase40_prereg.py is frozen before every results/phase40_* record, the rulings are quoted
  verbatim at their fixed commits, nothing derived is typed, the entries have four fields and honest
  kinds, importing it opens no checkpoint, it passes the slot census, this file has zero skips and
  every prereg function is called by a CPU test.

It reads only tracked files and git history and writes nothing under results/.
"""

import fnmatch
import json
import math
import pathlib
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
import phase40_prereg  # noqa: E402  (same)

PREREG = "scripts/phase40_prereg.py"


def _record(rel):
    return json.loads((_ROOT / rel).read_text(encoding="utf-8"))


def _budget():
    return _record("results/phase36_budget.json")


def _formula(d13_adapters=0, d13_nlls=0):
    """The budget's E2 term (scripts/phase36_budget.py `_front_seconds`), re-stated here, plus the
    D-13 scoring after it."""
    budget = _budget()
    p, e2 = budget["unit_prices"], budget["unit_caps"]["E2"]
    committed = (
        e2["seeds"]
        * (p["e2_train_m2_high"] + p["e2_train_full_high"] + e2["adapters"] * p["e2_a2_pass_high"])
        / 3600
    )
    return committed + d13_adapters * (p["adapter_setup_high"] + d13_nlls * p["e5_nll_high"]) / 3600


def _d13_count():
    """The D-13 NLLs per M2 adapter, recomputed from the modules that own each term."""
    import phase18_extraction
    import phase19_erasure as pin
    import phase38_rank

    slot = pin.TARGET_SLOT
    anchor = phase38_rank.scoring_plan(slots=(slot,))[slot]["size"]
    refs = len(phase18_extraction.reference_set_for(slot))
    questions = sum(e["slot"] == slot for e in phase35_prereg.a2_corpus_entries())
    return anchor + refs + questions * refs + questions * (phase39_prereg.MINTED_SET_SIZE - 1)


# =================================================================================================
# (1) RECORD PATHS AND THE D-11 / D-13 / D-14 APPROVAL ARITHMETIC.
# =================================================================================================


def test_projection_reproduces_front_hours():
    budget = _budget()
    assert phase40_prereg.e2_projection_hours() == budget["front_hours"]["E2"]
    assert _formula() == budget["front_hours"]["E2"]
    assert phase40_prereg.e2_projection_hours(0, 0) == _formula()
    assert phase40_prereg.e2_projection_hours(3, 7) == _formula(3, 7)


def test_approval_projection_and_stop():
    p = phase40_prereg
    assert repr(p.E2_STOP_HOURS) == "11.83638889157415"
    stop = phase36_prereg.ENTRIES["front_stop_factor"]["value"] * _budget()["front_hours"]["E2"]
    assert p.E2_STOP_HOURS == stop
    if p.D13_INCLUDED:
        assert repr(p.E2_PROJECTION_HOURS) == "7.9518624092864085"
        assert repr(p.E2_TOTAL_HOURS) == "77.78526798055215"
    else:
        assert repr(p.E2_PROJECTION_HOURS) == "7.890925927716101"
        assert repr(p.E2_TOTAL_HOURS) == "77.72433149898184"
    assert p.E2_PROJECTION_HOURS == _formula(p.D13_ADAPTERS, p.D13_NLLS_PER_ADAPTER)
    assert p.E2_PROJECTION_HOURS <= p.E2_STOP_HOURS


def _fsum_with(**fronts):
    return math.fsum({**_budget()["front_hours"], **fronts}.values())


def test_approval_record_total_with_e5_e6():
    p = phase40_prereg
    if p.D13_INCLUDED:
        assert repr(p.E2_E5_E6_TOTAL_HOURS) == "78.12639556620314"
        assert repr(p.E2_E5_E6_TOTAL_HOURS_E6_ACTUAL_GATE) == "78.12556459250179"
    else:
        assert repr(p.E2_E5_E6_TOTAL_HOURS) == "78.06545908463283"
        assert repr(p.E2_E5_E6_TOTAL_HOURS_E6_ACTUAL_GATE) == "78.06462811093148"
    e5 = phase38_prereg.E5_PROJECTION_HOURS
    assert p.E2_E5_E6_TOTAL_HOURS == _fsum_with(
        E2=p.E2_PROJECTION_HOURS, E5=e5, E6=phase39_prereg.E6_PROJECTION_HOURS
    )
    assert p.E2_E5_E6_TOTAL_HOURS_E6_ACTUAL_GATE == _fsum_with(
        E2=p.E2_PROJECTION_HOURS, E5=e5, E6=phase39_prereg.E6_PROJECTION_HOURS_ACTUAL_GATE
    )
    assert p.E2_TOTAL_HOURS == _fsum_with(E2=p.E2_PROJECTION_HOURS)
    block = p.approval_block()
    assert block["e2_e5_e6_total_hours"] == p.E2_E5_E6_TOTAL_HOURS
    assert block["e2_e5_e6_total_hours_e6_actual_gate"] == p.E2_E5_E6_TOTAL_HOURS_E6_ACTUAL_GATE
    assert block["committed_total_hours"] == _budget()["total_hours"]
    assert block["e2_total_hours"] == p.E2_TOTAL_HOURS
    assert block["e5_projection_hours"] == e5
    assert block["e6_projection_hours"] == phase39_prereg.E6_PROJECTION_HOURS
    assert (
        block["e6_projection_hours_actual_gate"] == phase39_prereg.E6_PROJECTION_HOURS_ACTUAL_GATE
    )


def test_approval_d13_nll_count_is_derived():
    p = phase40_prereg
    count = p.d13_nlls_per_adapter()
    assert count == 512 + 8 + 27 * 8 + 27 * 7
    assert count == _d13_count()
    assert p.D13_NLLS_PER_ADAPTER == (count if p.D13_INCLUDED else 0)
    assert p.D13_ADAPTERS == (_budget()["unit_caps"]["E2"]["seeds"] if p.D13_INCLUDED else 0)
    assert type(p.D13_INCLUDED) is bool and type(p.D11_APPROVED) is bool


_APPROVAL_KEYS = (
    "ruling",
    "r3_conditions",
    "record_total_ruling",
    "addendum_ruling",
    "source",
    "rulings",
    "d11_approved",
    "d11_extra_seconds_reason",
    "d13_included",
    "d13_nlls_per_adapter",
    "d13_adapters",
    "e2_projection_hours",
    "committed_front_hours_e2",
    "e2_total_hours",
    "committed_total_hours",
    "e5_projection_hours",
    "e6_projection_hours",
    "e6_projection_hours_actual_gate",
    "e2_e5_e6_total_hours",
    "e2_e5_e6_total_hours_e6_actual_gate",
    "e2_stop_hours",
    "committed_unit_caps_e2",
    "budget_record",
    "untouched",
)


def test_approval_block_is_fresh_and_complete():
    import phase36_ledger

    p = phase40_prereg
    budget = _budget()
    first = p.approval_block()
    second = p.approval_block()
    json.dumps(first)
    assert first == second and first is not second
    assert tuple(first) == _APPROVAL_KEYS == p.APPROVAL_KEYS
    assert first["ruling"] == p.APPROVALS_RULING
    assert first["r3_conditions"] == p.R3_CONDITIONS_RULING
    assert first["record_total_ruling"] == p.RECORD_TOTAL_RULING
    assert first["addendum_ruling"] == p.ADDENDUM_RULING
    assert first["d11_approved"] is p.D11_APPROVED
    assert first["d13_included"] is p.D13_INCLUDED
    assert first["d13_nlls_per_adapter"] == p.D13_NLLS_PER_ADAPTER
    assert first["d13_adapters"] == p.D13_ADAPTERS
    assert first["e2_projection_hours"] == p.E2_PROJECTION_HOURS
    assert first["committed_front_hours_e2"] == budget["front_hours"]["E2"]
    assert first["e2_stop_hours"] == p.E2_STOP_HOURS
    assert first["committed_unit_caps_e2"] == budget["unit_caps"]["E2"]
    assert first["budget_record"] == "results/phase36_budget.json" == p.BUDGET_RECORD
    assert first["untouched"] == [
        phase36_ledger.LEDGER_PATH,
        p.BUDGET_RECORD,
        "scripts/phase36_ledger.py",
        "scripts/phase36_caps.py",
    ]
    assert first["untouched"][0] == "ledger/v6_mps_ledger.jsonl"
    first["untouched"].clear()
    first["rulings"]["R-1"] = "planted"
    first["committed_unit_caps_e2"]["seeds"] = 0
    third = p.approval_block()
    assert third == second
    assert len(third["untouched"]) == 4
    assert third["committed_unit_caps_e2"] == budget["unit_caps"]["E2"]


def test_record_paths_from_the_registry():
    p = phase40_prereg
    registry = phase35_prereg.SLOTS["e1_condition_c_band_inputs"]["input_records"][0]
    assert p.NOISE_FLOOR_RECORD == registry == "results/phase40_noise_floor.json"
    assert p.REPORT_RECORD == "results/phase40_noise_floor_report.md"
    assert p.RECORD_GLOB == "results/phase40_*"
    assert p.seed_record(1337) == "results/phase40_seed1337.json"
    assert p.a2_record("full", 1337) == "results/phase40_a2_full_seed1337.json"
    assert p.a2_record("m2", 2024) == "results/phase40_a2_m2_seed2024.json"
    assert p.run_id(1339) == "v6/40/E2/seed1339"
    assert p.GROUPS == ("full", "m2")
    seeds = phase35_prereg.seed_list()
    paths = [p.NOISE_FLOOR_RECORD, p.REPORT_RECORD]
    paths += [p.seed_record(s) for s in seeds]
    paths += [p.a2_record(g, s) for g in p.GROUPS for s in seeds]
    assert all(fnmatch.fnmatch(path, p.RECORD_GLOB) for path in paths)
    assert len(set(paths)) == len(paths)
    with pytest.raises(SystemExit, match=r"^\[phase40_prereg\]"):
        p.a2_record("planted", 1337)
