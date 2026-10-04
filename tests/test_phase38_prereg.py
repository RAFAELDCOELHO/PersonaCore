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
import random
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


# =================================================================================================
# (2) THE PURE DEFINITIONS (D-12, D-15, D-18, D-28..D-30).
# =================================================================================================


def _exposure_rank(nll, taught):
    import phase18_extraction  # torch at import: inside the test only

    return phase18_extraction.exposure_rank(
        nll, taught_value=taught, reduction="mean", length_spread=0
    )


def test_rank_in_prefix_breaks_ties_by_string():
    tie_before = {"a": 1.0, "t": 2.0, "b": 2.0, "c": 3.0}
    assert phase38_prereg.rank_in_prefix(tie_before, "t", ["a", "b", "c"]) == 3
    tie_after = {"a": 1.0, "t": 2.0, "z": 2.0, "c": 3.0}
    assert phase38_prereg.rank_in_prefix(tie_after, "t", ["a", "z", "c"]) == 2
    pad = {"x": 9.0, "y": 9.5}
    assert _exposure_rank({**tie_before, **pad}, "t")["rank"] == 3
    assert _exposure_rank({**tie_after, **pad}, "t")["rank"] == 2
    assert phase38_prereg.rank_in_prefix({**tie_before, **pad}, "t", ["a", "b", "c", "x", "y"]) == 3


def test_rank_in_prefix_refuses_malformed_sets():
    nll = {"a": 1.0, "t": 2.0}
    for taught, members in (("q", ["a"]), ("t", ["t", "a"]), ("t", ["a", "a"]), ("t", ["b"])):
        with pytest.raises(SystemExit, match=r"^\[phase38_prereg\]"):
            phase38_prereg.rank_in_prefix(nll, taught, members)


def test_rank_in_prefix_equals_exposure_rank_on_random_tied_sets():
    rng = random.Random(0)
    letters = "abcdefghijklmnopqrstuvwxyz"
    for _ in range(200):
        size = rng.randint(6, 8)
        keys = rng.sample([a + b for a in letters for b in letters], size)
        nll = {key: rng.choice((0.5, 1.25, 2.0)) for key in keys}
        taught = rng.choice(keys)
        committed = _exposure_rank(nll, taught)
        rank = phase38_prereg.rank_in_prefix(nll, taught, [c for c in nll if c != taught])
        assert rank == committed["rank"], (nll, taught)
        assert phase38_prereg.exposure_bits(rank, len(nll)) == committed["exposure_bits"]


def test_exposure_bits():
    assert phase38_prereg.exposure_bits(1, 512) == 9.0
    assert phase38_prereg.exposure_bits(2, 8) == 2.0
    for rank, size in ((0, 8), (9, 8)):
        with pytest.raises(SystemExit, match=r"^\[phase38_prereg\]"):
            phase38_prereg.exposure_bits(rank, size)


def test_moved_and_left_top_eighth():
    assert phase38_prereg.moved(2, 1) is True
    assert phase38_prereg.moved(1, 1) is False
    assert phase38_prereg.moved(3, 2) is False
    assert phase38_prereg.moved(4, 2) is True
    assert phase38_prereg.left_top_eighth(1, 8) is False
    assert phase38_prereg.left_top_eighth(2, 8) is True
    assert phase38_prereg.left_top_eighth(64, 512) is False
    assert phase38_prereg.left_top_eighth(65, 512) is True


def test_first_event_and_relation():
    flags = {0: False, 8: False, 16: True, 32: True, 64: False, 78: True}
    assert phase38_prereg.first_event(flags) == 16
    assert phase38_prereg.first_event(dict.fromkeys(phase38_prereg.PREFIXES, False)) is None
    with pytest.raises(SystemExit, match=r"^\[phase38_prereg\]"):
        phase38_prereg.first_event({**flags, 7: True})
    with pytest.raises(SystemExit, match=r"^\[phase38_prereg\]"):
        phase38_prereg.first_event({k: v for k, v in flags.items() if k != 78})
    assert phase38_prereg.relation(16, 64) == "BEFORE"
    assert phase38_prereg.relation(64, 64) == "SAME"
    assert phase38_prereg.relation(78, 64) == "AFTER"
    assert phase38_prereg.relation(None, 64) == "NEVER"
    assert phase38_prereg.relation(16, None) == "REFERENCE_NEVER_IN_GRID"
    assert phase38_prereg.relation(None, None) == "REFERENCE_NEVER_IN_GRID"
    assert set(phase38_prereg.ENTRIES["event_relation"]["value"]) == {
        "BEFORE",
        "SAME",
        "AFTER",
        "NEVER",
        "REFERENCE_NEVER_IN_GRID",
    }


def test_components_sha256_reproduces_the_probe_e1_digest():
    prefix = _record("results/phase19_collateral_curve.json")["ordered_prefix"]
    digest = _record("results/phase36_probe_e1.json")["configuration"]["components_sha256"]
    assert phase38_prereg.components_sha256(prefix) == digest
    assert digest == "a7cc22715d64def87795d730a69698206294963b2ed15b9badef495c82effda7"
    assert phase38_prereg.components_sha256(prefix[:-1]) != digest


# =================================================================================================
# (3) THE COMMITTED A2 COUNTS, THEIR EVENTS AND THE D-33 AUDIT (D-13, D-14, D-33).
# =================================================================================================

# 38-RESEARCH "A2 counts": k = 0, 8, 16, 32, 64, 78; then (first damaged, first collapsed).
_A2 = {
    "pet_name": ((27, 24, 18, 2, 0, 0), 16, 64),
    "person_name": ((26, 18, 10, 1, 0, 0), 16, 64),
    "cat_name": ((27, 27, 27, 27, 6, 7), 64, None),
    "sibling_name": ((27, 27, 22, 10, 0, 0), 32, 64),
    "hometown": ((21, 7, 3, 1, 0, 0), 8, 64),
    "street": ((27, 27, 24, 11, 0, 0), 32, 64),
    "birth_year": ((18, 14, 13, 14, 11, 8), 78, None),
    "house_number": ((24, 24, 24, 10, 6, 5), 32, None),
}


@pytest.fixture(scope="module")
def a2():
    return phase38_prereg.a2_counts()


def test_a2_counts_and_events_reproduce_the_research_table(a2):
    assert list(a2) == list(phase38_prereg.SLOTS)
    for slot, (counts, damaged, collapsed) in _A2.items():
        row = a2[slot]
        assert row["n_questions"] == 27, slot
        assert tuple(row["counts"][k] for k in phase38_prereg.PREFIXES) == counts, slot
        assert phase38_prereg.first_damage(row["counts"], row["n_questions"]) == damaged, slot
        assert phase38_prereg.first_collapse(row["counts"]) == collapsed, slot
    person = a2["person_name"]["counts"]
    drop = person[0] / 27 - person[8] / 27
    assert drop == phase38_prereg.MARGIN  # an exact tie, decided by the strict >
    json.dumps(a2)


def test_drop_formula_audit_on_the_committed_records(a2):
    audit = phase38_prereg.drop_formula_audit(a2)
    assert audit["criterion"] is False
    assert audit["formula"] == "pre/n - post/n"
    cells = {(c["slot"], c["k"]): c for c in audit["cells"]}
    assert len(cells) == len(phase38_prereg.SLOTS) * (len(phase38_prereg.PREFIXES) - 1)
    summary = _record("results/erasure_kstar_summary.json")["checkpoints"]
    for k in ("8", "16", "32", "64"):
        for slot, row in summary[k]["nontarget"].items():
            assert cells[(slot, int(k))]["rate_drop"] == row["delta"], (slot, k)
    differing = {tuple(c) for c in audit["differing"]}
    nontarget = {(s, k) for s, k in differing if s != "pet_name" and k != 78}
    assert nontarget == {
        ("hometown", 8),
        ("hometown", 16),
        ("sibling_name", 16),
        ("street", 16),
        ("person_name", 32),
    }
    assert {(s, k) for s, k in differing if s == "pet_name"} == {("pet_name", 8), ("pet_name", 16)}
    assert cells[("pet_name", 8)]["rate_drop"] == 0.11111111111111116
    assert cells[("pet_name", 8)]["count_drop"] == 0.1111111111111111
    assert cells[("pet_name", 16)]["rate_drop"] == 0.33333333333333337
    assert cells[("pet_name", 16)]["count_drop"] == 0.3333333333333333
    assert not [cell for cell in differing if cell[1] == 78]
    assert audit["flips"] == []
    assert audit["exact_ties"] == [["person_name", 8]]
    json.dumps(audit)

    # NON-VACUITY: at a margin sitting between the two formulas, the flip is caught and named.
    margin = cells[("hometown", 8)]["count_drop"]
    assert margin == 0.5185185185185185
    planted = phase38_prereg.drop_formula_audit(a2, margin=margin)
    cell = next(c for c in planted["cells"] if (c["slot"], c["k"]) == ("hometown", 8))
    assert cell["damaged_rate"] is True and cell["damaged_count"] is False
    assert ["hometown", 8] in planted["flips"]


# =================================================================================================
# (4) THE 64 COMMITTED GATE RANKS (D-18).
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
_ADAPTER_OFF_RANKS = (5, 4, 3, 4, 5, 3, 3, 5)
_N_REFERENCES = (8, 8, 7, 7, 7, 6, 7, 6)


def test_committed_gate_ranks_reproduce_the_research_table():
    gate = phase38_prereg.committed_gate_ranks()
    assert list(gate) == list(phase38_prereg.READINGS)
    assert phase38_prereg.SLOTS == _SLOT_ORDER
    for reading, rows in gate.items():
        assert list(rows) == list(_SLOT_ORDER), reading
        for slot, n in zip(_SLOT_ORDER, _N_REFERENCES, strict=True):
            assert rows[slot]["n_references"] == n, (reading, slot)
            assert isinstance(rows[slot]["nll_mean"], float), (reading, slot)
    for slot, rank in zip(_SLOT_ORDER, _ADAPTER_OFF_RANKS, strict=True):
        assert gate["adapter_off"][slot]["rank"] == rank, slot
    for reading in ("k0", "k8", "k16", "k32", "k64", "k78", "M2"):
        for slot in _SLOT_ORDER:
            moved_pet = slot == "pet_name" and reading in ("k78", "M2")
            assert gate[reading][slot]["rank"] == (2 if moved_pet else 1), (reading, slot)
    json.dumps(gate)
