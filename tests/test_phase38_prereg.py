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

import ast
import fnmatch
import hashlib
import json
import math
import pathlib
import random
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

import phase14_factset  # noqa: E402  (scripts/ is not a package)
import phase19_floor  # noqa: E402  (same)
import phase35_prereg  # noqa: E402  (same)
import phase36_prereg  # noqa: E402  (same)
import phase38_prereg  # noqa: E402  (same)

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
        "ALREADY_AT_K0",
        "UNREACHABLE_AT_SIZE",
    }


def test_left_top_eighth_already_true_at_k0_is_its_own_outcome():
    # WR-01, Rafael's ruling: birth_year at |R| = 220 with rank_0 >= 28 starts outside the top
    # eighth; that is ALREADY_AT_K0 against both references, never BEFORE.
    size = 220
    assert phase38_prereg.left_top_eighth(28, size) is True
    assert phase38_prereg.left_top_eighth(27, size) is False
    event = phase38_prereg.first_event(
        {k: phase38_prereg.left_top_eighth(28, size) for k in phase38_prereg.PREFIXES}
    )
    assert event == 0
    for reference in (8, 32, 64, None):
        assert phase38_prereg.relation(event, reference) == "ALREADY_AT_K0"
    # rank_0 = 27 is inside the top eighth at k = 0; leaving it at k = 8 is an ordinary event.
    ranks = {0: 27, 8: 28, 16: 28, 32: 40, 64: 90, 78: 100}
    later = phase38_prereg.first_event(
        {k: phase38_prereg.left_top_eighth(r, size) for k, r in ranks.items()}
    )
    assert later == 8
    assert phase38_prereg.relation(later, 64) == "BEFORE"


def test_moved_that_cannot_fire_at_the_size_is_unreachable_not_never():
    # WR-01, Rafael's ruling: at |R| = 8 with rank_0 >= 5, 2 x rank_0 > |R| and "moved" cannot
    # fire; that is UNREACHABLE_AT_SIZE, and NEVER stays "could have moved and did not".
    size = 8
    assert phase38_prereg.moved_reachable(5, size) is False
    assert phase38_prereg.moved_reachable(4, size) is True
    assert phase38_prereg.moved_reachable(1, 512) is True
    flags = {k: phase38_prereg.moved(size, 5) for k in phase38_prereg.PREFIXES}
    event = phase38_prereg.first_event(flags)
    assert event is None
    reachable = phase38_prereg.moved_reachable(5, size)
    for reference in (64, None):
        assert phase38_prereg.relation(event, reference, reachable=reachable) == (
            "UNREACHABLE_AT_SIZE"
        )
    assert phase38_prereg.relation(None, 64, reachable=True) == "NEVER"
    assert phase38_prereg.relation(16, 64, reachable=True) == "BEFORE"
    with pytest.raises(SystemExit, match=r"^\[phase38_prereg\]"):
        phase38_prereg.relation(16, 64, reachable=False)
    for rank_0 in (0, 9):
        with pytest.raises(SystemExit, match=r"^\[phase38_prereg\]"):
            phase38_prereg.moved_reachable(rank_0, size)


def test_the_two_wr01_outcomes_are_stated_in_d12_and_d29():
    moved = phase38_prereg.ENTRIES["rank_moved"]["derivation"]
    eighth = phase38_prereg.ENTRIES["left_top_eighth"]["derivation"]
    relation = phase38_prereg.ENTRIES["event_relation"]["derivation"]
    assert "UNREACHABLE_AT_SIZE" in moved and "rank_0" in moved
    assert "ALREADY_AT_K0" in eighth and "rank_0" in eighth
    assert "UNREACHABLE_AT_SIZE" in relation and "ALREADY_AT_K0" in relation


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


def test_exposure_rows_refuse_a_missing_slot():
    rows = _record("results/phase19_arm_erased.json")["exposure"]
    assert set(phase38_prereg._exposure_rows(rows)) == set(phase38_prereg.SLOTS)
    with pytest.raises(SystemExit, match=r"^\[phase38_prereg\]"):
        phase38_prereg._exposure_rows(rows[1:])


# =================================================================================================
# (5) ANCESTRY (SC4, T-38-01): frozen before every results/phase38_* record, the minting record
# included. Honest at zero records and after them.
# =================================================================================================


def _strictly_before(x, y):
    run = subprocess.run(("git", "merge-base", "--is-ancestor", x, y), cwd=_ROOT, check=False)
    return x != y and run.returncode == 0


def _first_add(path):
    return _git("log", "--diff-filter=A", "--format=%H", "--", path).split()[-1]


def _phase38_records():
    return sorted(_git("ls-files", "results/phase38_*").split())


def test_phase38_prereg_is_frozen_before_every_phase38_record():
    _assert_frozen_before(PREREG, _phase38_records())
    # NON-VACUITY (natural RED): the v6.0 pre-registration was added before this one existed.
    with pytest.raises(subprocess.CalledProcessError):
        _assert_frozen_before(PREREG, ["scripts/phase35_prereg.py"])


def test_this_test_file_is_first_added_before_every_phase38_record():
    # Only the FIRST add: a later fix to this file must not redden the guard forever.
    mine = _first_add("tests/test_phase38_prereg.py")
    for record in _phase38_records():
        assert _strictly_before(mine, _first_add(record)), record
    # NON-VACUITY: the same check against a file added long before this one is False.
    assert not _strictly_before(mine, _first_add("scripts/phase35_prereg.py"))


def test_records_at_commit_is_true_at_the_first_commit():
    first = _git("log", "--format=%H", "--", PREREG).split()[-1]
    at_first = _git("ls-tree", "-r", "--name-only", first, "--", "results/").split()
    assert at_first, "meta-guard: the first commit's results/ tree is empty, the check is vacuous"
    assert not [p for p in at_first if p.startswith("results/phase38_")]
    assert phase38_prereg.RECORDS_AT_COMMIT == 0


# =================================================================================================
# (6) PATHS AND INPUTS RESOLVE FROM THE MODULES THAT OWN THEM (D-02, D-05, D-09, D-24).
# =================================================================================================


def test_record_paths_and_inputs_resolve_from_the_modules():
    import phase17_persona_gate  # torch at import: inside the test only
    import phase17_personas
    import phase19_erasure as pin
    import phase19_run

    from personacore.tokenizer import from_json

    assert phase38_prereg.MINTING_GLOB in phase35_prereg.V6_RESULT_PATHS
    assert phase38_prereg.RECORD_GLOB in phase35_prereg.V6_RESULT_PATHS
    assert phase38_prereg.MINTING_RECORD == "results/phase38_minting.json"
    matching = [
        p for p in phase38_prereg.RECORDS if fnmatch.fnmatch(p, phase38_prereg.MINTING_GLOB)
    ]
    assert matching == [phase38_prereg.MINTING_RECORD]

    def rel(path):
        return path.resolve().relative_to(_ROOT).as_posix()

    assert phase38_prereg.ERASED_RECORD == rel(pin.arm_record_path("erased"))
    assert phase38_prereg.RETRAIN_RECORD == rel(pin.arm_record_path("retrain"))
    assert phase38_prereg.CURVE_RECORD == rel(phase19_run.TARGET_CURVE_PATH)
    assert phase38_prereg.PHASE17_REPORT == rel(phase17_persona_gate.REPORT_PATH)
    assert phase38_prereg.BUDGET_RECORD == "results/phase36_budget.json"
    assert phase38_prereg.SLOTS == tuple(phase17_personas.CORE_SLOTS)
    for path in (
        phase38_prereg.KSTAR_SUMMARY,
        phase38_prereg.TARGET_SCORES,
        phase38_prereg.RETRAIN_SCORES,
        phase38_prereg.ADAPTER_OFF_RECORD,
        phase38_prereg.ADAPTER_ON_RECORD,
        phase38_prereg.PROBE_E1_RECORD,
    ):
        assert _git("ls-files", "--error-unmatch", path) == path

    # D-02 / D-09: every value in both inclusive numeric ranges has the taught value's token count.
    tok = from_json(_ROOT / "artifacts" / "tokenizer.json")
    taught = {fact.slot: fact.value for fact in phase14_factset.LOCKED_FACTS}
    for slot, (lo, hi) in phase38_prereg.NUMERIC_RANGES.items():
        want = len(tok.encode(taught[slot]))
        counts = {len(tok.encode(str(v))) for v in range(lo, hi + 1)}
        assert counts == {want}, slot

    # D-24: the pinned digest is the committed report's bytes at HEAD.
    blob = subprocess.run(
        ("git", "show", f"HEAD:{phase38_prereg.PHASE17_REPORT}"),
        cwd=_ROOT,
        capture_output=True,
        check=True,
    ).stdout
    assert hashlib.sha256(blob).hexdigest() == phase38_prereg.PHASE17_REPORT_SHA256


# =================================================================================================
# (7) THE D-21 RULING, QUOTED AT ITS FIXED COMMIT; THE APPROVAL BLOCK (D-22).
# =================================================================================================

_CONTEXT_PATH = ".planning/phases/38-exposure-rank-at-larger-minted-sets/38-CONTEXT.md"


def _d21_quote():
    text = _git("show", f"255380f:{_CONTEXT_PATH}")
    bullet = next(line for line in text.splitlines() if line.startswith("- **D-21:"))
    return bullet.split('Rafael: "', 1)[1].split('"', 1)[0]


def test_d21_ruling_is_quoted_verbatim():
    quote = _d21_quote()
    assert len(quote.split()) > 5, "meta-guard: the D-21 bullet parsed too short"
    assert quote == phase38_prereg.D21_RULING
    assert quote in phase38_prereg.ENTRIES["e5_prefix_cap_approval"]["derivation"]
    assert phase38_prereg.ENTRIES["e5_prefix_cap_approval"]["value"] == 8

    block = phase38_prereg.approval_block()
    assert set(block) == {
        "ruling",
        "source",
        "approved_prefixes",
        "committed_prefix_cap",
        "readings",
        "e5_projection_hours",
        "committed_front_hours_e5",
        "e5_total_hours",
        "committed_total_hours",
        "e5_stop_hours",
        "budget_record",
    }
    budget = _budget()
    assert block["approved_prefixes"] == phase38_prereg.APPROVED_E5_PREFIXES
    assert block["committed_prefix_cap"] == phase38_prereg.COMMITTED_PREFIX_CAP
    assert block["e5_projection_hours"] == phase38_prereg.E5_PROJECTION_HOURS
    assert block["e5_total_hours"] == phase38_prereg.E5_TOTAL_HOURS
    assert block["e5_stop_hours"] == phase38_prereg.E5_STOP_HOURS
    assert block["committed_front_hours_e5"] == budget["front_hours"]["E5"]
    assert block["committed_total_hours"] == budget["total_hours"]
    assert block["budget_record"] == phase38_prereg.BUDGET_RECORD


# =================================================================================================
# (8) NOTHING DERIVED IS TYPED (T-38-02).
# =================================================================================================


def test_no_derived_value_is_typed_in_the_prereg(tmp_path):
    budget = _budget()
    seeds = {
        phase35_prereg.seed_list()[0],
        phase35_prereg.ENTRIES["e5_max_set_size"]["value"],
    }
    floats = {
        phase38_prereg.E5_PROJECTION_HOURS,
        phase38_prereg.E5_TOTAL_HOURS,
        phase38_prereg.E5_STOP_HOURS,
        phase38_prereg.MARGIN,
        budget["front_hours"]["E5"],
        budget["total_hours"],
        phase19_floor.NONTARGET_NOISE_FLOOR,
    }
    assert all(type(f) is float for f in floats), "meta-guard: a census value is not a float"
    real = _ROOT / PREREG
    before = real.read_bytes()
    source = before.decode("utf-8")
    assert _literal_failures(source, seeds, floats, set()) == []
    for name, line in (
        ("stop.py", f"\nX = {phase38_prereg.E5_STOP_HOURS!r}\n"),
        ("seed.py", f"\nS = {phase35_prereg.seed_list()[0]!r}\n"),
    ):
        planted = _planted(tmp_path, source, source + line, name)
        assert _literal_failures(planted, seeds, floats, set()), name
    assert real.read_bytes() == before


# =================================================================================================
# (9) ENTRIES: EXACTLY FOUR FIELDS, NO PROPOSER, HONEST KINDS (T-38-03).
# =================================================================================================


def _good_entry():
    return {"value": 1, "derivation": "d", "kind": "derived", "source": "s"}


def test_entries_have_exactly_four_fields_and_no_proposer(tmp_path):
    assert phase38_prereg.ENTRY_FIELDS is phase35_prereg.ENTRY_FIELDS
    assert phase38_prereg.KINDS is phase35_prereg.KINDS
    for name, entry in phase38_prereg.ENTRIES.items():
        assert set(entry) == {"value", "derivation", "kind", "source"}, name
    with pytest.raises(TypeError):
        phase38_prereg.ENTRIES["planted"] = {}
    assert phase38_prereg._prove_entries() is None

    phase38_prereg._prove_entry("ok", _good_entry())
    refused = (
        {**_good_entry(), "proposer": "Rafael"},
        {**_good_entry(), "adopted_by": "Rafael"},
        {k: v for k, v in _good_entry().items() if k != "source"},
        {**_good_entry(), "kind": "guess"},
        {**_good_entry(), "derivation": ""},
        {**_good_entry(), "value": phase38_prereg.FORBIDDEN_PHRASE},
        [1],
    )
    for entry in refused:
        with pytest.raises(SystemExit, match=r"^\[phase38_prereg\]"):
            phase38_prereg._prove_entry("x", entry)

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
        source, first.lineno, first.col_offset + 1, phase38_prereg.FORBIDDEN_PHRASE
    )
    ast.parse(planted_phrase)
    assert _entry_string_failures(_planted(tmp_path, source, planted_phrase, "phrase.py"))
    assert real.read_bytes() == before


def test_prove_and_read():
    with pytest.raises(SystemExit, match=r"^\[phase38_prereg\] x$"):
        phase38_prereg._prove(False, "x")
    assert phase38_prereg._prove(True, "x") is None
    read = phase38_prereg._read(phase38_prereg.ERASED_RECORD)
    assert isinstance(read, dict) and "pre_erasure" in read


def test_preferences_are_labelled():
    kinds = {name: entry["kind"] for name, entry in phase38_prereg.ENTRIES.items()}
    derived = {"generation_damaged", "e5_projection_hours", "e5_total_hours", "e5_stop_hours"}
    assert {n for n, k in kinds.items() if k == "derived"} == derived
    assert {n for n, k in kinds.items() if k == "preference"} == set(kinds) - derived
    assert len(kinds) == 16
    for name, entry in phase38_prereg.ENTRIES.items():
        assert re.search(r"D-\d\d", entry["derivation"]), name


def test_minting_rule_entry_states_the_whole_rule():
    value = phase38_prereg.E5_MINTING_RULE["value"]
    assert set(value) == {
        "generator",
        "surface",
        "stream",
        "deal",
        "exclusions",
        "name_filters",
        "numeric_filters",
        "match",
        "questions",
        "clearance",
        "stop",
        "continuation",
        "uniqueness",
        "neighbour",
        "numeric",
        "sets",
    }
    generator = value["generator"]
    assert generator["onsets"] == phase38_prereg.ONSETS
    assert generator["nuclei"] == phase38_prereg.NUCLEI
    assert generator["codas"] == phase38_prereg.CODAS
    assert generator["max_syllables"] == phase38_prereg.MAX_SYLLABLES
    assert "seed_list()[0]" in generator["seed"]  # by reference, never the literal (D-01)
    assert "rng.random()" in generator["draw"]
    assert value["name_filters"] == phase38_prereg.NAME_FILTERS
    assert value["numeric_filters"] == phase38_prereg.NUMERIC_FILTERS
    assert value["sets"]["nested_sizes"] == phase38_prereg.NESTED_SIZES
    assert phase38_prereg.NESTED_SIZES[-1] == phase35_prereg.ENTRIES["e5_max_set_size"]["value"]
    assert value["stop"]["slack_per_slot"] == phase38_prereg.SLACK_PER_SLOT
    assert value["stop"]["max_draws"] == phase38_prereg.MAX_DRAWS
    assert value["stream"]["rejections"] == phase38_prereg.STREAM_REJECTIONS
    assert value["deal"]["order"] == phase38_prereg.NAME_SLOTS
    assert value["clearance"]["report_sha256"] == phase38_prereg.PHASE17_REPORT_SHA256
    assert dict(value["numeric"]["ranges"]) == dict(phase38_prereg.NUMERIC_RANGES)
    assert value["surface"]["fixed_suffix"] is None


# =================================================================================================
# (10) CPU-ONLY AT IMPORT, THE SLOT CENSUS, ZERO SKIPS, EVERY FUNCTION CALLED (T-38-05).
# =================================================================================================


def test_the_prereg_imports_without_torch():
    probe = (
        "import sys; sys.path.insert(0, 'scripts'); import phase38_prereg; "
        f"print(*[name in sys.modules for name in {_HEAVY!r}])"
    )
    out = subprocess.run(
        [sys.executable, "-c", probe], cwd=_ROOT, capture_output=True, text=True, check=True
    )
    assert out.stdout.split() == ["False"] * len(_HEAVY), out.stdout


def test_phase38_scripts_pass_the_slot_census():
    paths = sorted(_SCRIPTS.glob("phase38_*.py"))
    assert paths, "meta-guard: no scripts/phase38_*.py, the census would be vacuous"
    sources = [(p.relative_to(_ROOT).as_posix(), p.read_text(encoding="utf-8")) for p in paths]
    assert _slot_census_failures(sources) == []


def test_no_skips_in_this_file(tmp_path):
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert _skip_failures(source) == []
    planted = source + '\n\ndef test_planted():\n    pytest.skip("x")\n'
    assert _skip_failures(_planted(tmp_path, source, planted, "skip.py"))


def test_every_phase38_prereg_function_has_a_cpu_test(tmp_path):
    real = _ROOT / PREREG
    before = real.read_bytes()
    source = before.decode("utf-8")
    test_source = pathlib.Path(__file__).read_text(encoding="utf-8")
    defs = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)]
    assert defs, "meta-guard: the prereg defines no function, the census would be vacuous"
    assert _untested_functions("phase38_prereg", source, test_source) == []

    planted = source + '\n\ndef planted_untested():\n    """Planted."""\n'
    copied = _planted(tmp_path, source, planted, "untested.py")
    assert _untested_functions("phase38_prereg", copied, test_source) == ["planted_untested"]
    assert real.read_bytes() == before


# =================================================================================================
# (11) THE MINTING RULE AS CODE (plan 38-02): the report parser, the exclusion sets, levenshtein,
# draw_name and mint_names under the global stop. Small per_slot only: the real 2048-per-slot mint
# is plan 04's (Pitfall 8).
# =================================================================================================


@pytest.fixture(scope="module")
def tok():
    from personacore.tokenizer import from_json

    return from_json(_ROOT / "artifacts" / "tokenizer.json")


@pytest.fixture(scope="module")
def parsed():
    text = (_ROOT / phase38_prereg.PHASE17_REPORT).read_text(encoding="utf-8")
    return phase38_prereg.parse_completions(text)


def _flat_questions(questions_by_slot):
    return tuple(q for slot in phase38_prereg.SLOTS for q in questions_by_slot[slot])


@pytest.fixture(scope="module")
def minted24(tok, parsed):
    completions, questions = parsed
    return phase38_prereg.mint_names(
        tok,
        completions,
        _flat_questions(questions),
        per_slot=24,
        seed=phase35_prereg.seed_list()[0],
    )


def test_parse_completions_on_the_tracked_report(parsed):
    import phase17_isolation  # torch at import: tests only

    completions, questions = parsed
    assert tuple(completions) == phase38_prereg.SLOTS
    assert tuple(questions) == phase38_prereg.SLOTS
    assert {len(c) for c in completions.values()} == {phase38_prereg.COMPLETIONS_PER_SLOT}
    assert sum(map(len, completions.values())) == phase38_prereg.COMPLETIONS_TOTAL
    held_out = phase17_isolation.held_out_by_slot()
    assert tuple(held_out) == phase38_prereg.SLOTS
    for slot in phase38_prereg.SLOTS:
        assert list(questions[slot]) == [item.question for item in held_out[slot]], slot
    assert sum(map(len, questions.values())) == 104
    text = (_ROOT / phase38_prereg.PHASE17_REPORT).read_text(encoding="utf-8")
    assert hashlib.sha256(text.encode("utf-8")).hexdigest() == (
        phase38_prereg.PHASE17_REPORT_SHA256
    )


def test_parse_completions_refuses_a_missing_line_or_header():
    text = (_ROOT / phase38_prereg.PHASE17_REPORT).read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    warm = next(i for i, line in enumerate(lines) if line.startswith("  - warm 2: `"))
    header = next(i for i, line in enumerate(lines) if line.startswith("### Slot `cat_name`"))
    for broken in (lines[:warm] + lines[warm + 1 :], lines[:header] + lines[header + 1 :]):
        with pytest.raises(SystemExit, match="D-24"):
            phase38_prereg.parse_completions("".join(broken))


def test_taught_anywhere_and_forbidden():
    taught = phase38_prereg.taught_anywhere()
    assert len(taught) == 118
    assert len(phase38_prereg.forbidden_for_substring()) == 123
    assert {fact.value for fact in phase14_factset.LOCKED_FACTS} <= taught
    assert taught <= phase38_prereg.forbidden_for_substring()


def test_levenshtein_witnesses():
    assert phase38_prereg.levenshtein("zorr", "zorp") == 1
    assert phase38_prereg.levenshtein("tarrowgate", "marrowgate") == 1
    assert phase38_prereg.levenshtein("abc", "abc") == 0
    assert phase38_prereg.levenshtein("", "ab") == 2
    assert phase38_prereg.levenshtein("kitten", "sitting") == 3


def test_draw_name_is_deterministic_lowercase_ascii():
    first = phase38_prereg.draw_name(random.Random(5))
    assert first == phase38_prereg.draw_name(random.Random(5))
    rng = random.Random(5)
    for _ in range(200):
        name = phase38_prereg.draw_name(rng)
        assert name and name.isascii() and name.isalpha() and name.islower(), name


def test_mint_names_holds_every_filter(tok, parsed, minted24):
    completions, questions = parsed
    flat = _flat_questions(questions)
    taught = phase38_prereg.taught_anywhere()
    lists = minted24["lists"]
    assert minted24["reached"] is True
    assert tuple(lists) == phase38_prereg.NAME_SLOTS
    by_slot = {fact.slot: fact.value for fact in phase14_factset.LOCKED_FACTS}
    assert minted24["taught_token_count"] == {
        slot: len(tok.encode(by_slot[slot])) for slot in phase38_prereg.NAME_SLOTS
    }
    norm = phase14_factset.normalize_for_match
    question_norm = [norm(q) for q in flat]
    for slot, values in lists.items():
        assert len(values) >= 24, slot
        assert len(set(values)) == len(values)
        for v in values:
            assert v.isascii() and v.isalpha() and v.islower() and " " not in v
            assert len(tok.encode(v)) == minted24["taught_token_count"][slot]
            assert v not in taught
            assert all(phase38_prereg.levenshtein(v, t) > 1 for t in taught), v
            assert phase14_factset.exact_match_clean(completions[slot], v), v
            assert not any(norm(v) in q for q in question_norm), v
    every = [v for values in lists.values() for v in values]
    pool = every + sorted(phase38_prereg.forbidden_for_substring())
    for v in every:
        assert not any(o != v and (norm(v) in norm(o) or norm(o) in norm(v)) for o in pool), v
    for slot in phase38_prereg.NAME_SLOTS:
        rejections = minted24["rejections"][slot]
        assert tuple(rejections) == phase38_prereg.NAME_FILTERS
        assert all(type(n) is int and n >= 0 for n in rejections.values())
    assert set(minted24["stream"]) == {"draws", "token_count", "duplicate"}
    assert minted24["stop_draw"] == minted24["stream"]["draws"]


def test_mint_names_is_deterministic(tok, parsed, minted24):
    completions, questions = parsed
    again = phase38_prereg.mint_names(
        tok,
        completions,
        _flat_questions(questions),
        per_slot=24,
        seed=phase35_prereg.seed_list()[0],
    )
    assert again == minted24


def test_mint_names_is_prefix_stable(tok, parsed, minted24):
    completions, questions = parsed
    small = phase38_prereg.mint_names(
        tok,
        completions,
        _flat_questions(questions),
        per_slot=8,
        seed=phase35_prereg.seed_list()[0],
    )
    assert small["reached"] is True
    assert small["stop_draw"] <= minted24["stop_draw"]
    for slot in phase38_prereg.NAME_SLOTS:
        short, long = small["lists"][slot], minted24["lists"][slot]
        assert len(short) >= 8
        assert long[: len(short)] == short, slot


def test_mint_names_reports_a_short_stream_without_raising(tok, parsed):
    completions, questions = parsed
    out = phase38_prereg.mint_names(
        tok,
        completions,
        _flat_questions(questions),
        per_slot=24,
        seed=phase35_prereg.seed_list()[0],
        max_draws=50,
    )
    assert out["reached"] is False
    assert out["stop_draw"] is None
    assert out["stream"]["draws"] == 50
    assert any(len(v) < 24 for v in out["lists"].values())


def test_screen_names_the_first_failing_shared_filter(tok):
    screen = phase38_prereg._new_screen(tok, ["what is your quillon street"], ["zorvex"])
    assert screen["substring_minted"] == ["zorvex"]
    assert len(screen["substring_forbidden"]) == 123
    assert phase38_prereg._screen(tok, "brakimo", 9, screen) == "over_budget"
    assert phase38_prereg._screen(tok, "quillon", 5, screen) == "in_question"
    assert phase38_prereg._screen(tok, "zorpik", 5, screen) == "substring_forbidden"
    assert phase38_prereg._screen(tok, "zorvexa", 5, screen) == "substring_minted"
    assert phase38_prereg._screen(tok, "rvex", 5, screen) == "substring_minted"
    assert phase38_prereg._screen(tok, "brakimo", 5, screen) is None
    screen["live"] = set()
    assert phase38_prereg._screen(tok, "brakimo", 5, screen) == "roundtrip"


# =================================================================================================
# (12) THE NUMERIC SLOTS, THE SEEDED SHUFFLE, THE NEIGHBOUR FLAGS, mint_all AND THE SET SIZES
# (D-08..D-10, D-26, D-27, D-31), and the random() AST gate (Pitfall 6, T-38-08).
# =================================================================================================


def test_max_value_tokens_matches_phase17():
    import phase17_personas  # torch at import: tests only

    assert phase38_prereg.MAX_VALUE_TOKENS == phase17_personas.MAX_VALUE_TOKENS


def test_seeded_shuffle_is_a_deterministic_fisher_yates():
    values = list(range(50))
    shuffled = phase38_prereg.seeded_shuffle(values, 1337)
    assert values == list(range(50))
    assert sorted(shuffled) == values
    assert shuffled != values
    assert shuffled == phase38_prereg.seeded_shuffle(values, 1337)
    assert shuffled != phase38_prereg.seeded_shuffle(values, 7)
    assert phase38_prereg.seeded_shuffle([], 1) == []


@pytest.fixture(scope="module")
def numeric(tok, parsed):
    completions, questions = parsed
    flat = _flat_questions(questions)
    years, year_rej = phase38_prereg.numeric_candidates(
        "birth_year", tok, completions, flat, accepted=[]
    )
    houses, house_rej = phase38_prereg.numeric_candidates(
        "house_number", tok, completions, flat, accepted=years
    )
    return years, year_rej, houses, house_rej


def test_numeric_candidates_birth_year_and_house_number(numeric):
    years, year_rej, houses, house_rej = numeric
    assert len(years) == 219
    assert years == sorted(years, key=int)
    assert all(1800 <= int(y) <= 2025 for y in years)
    assert year_rej == {f: (7 if f == "excluded" else 0) for f in phase38_prereg.NUMERIC_FILTERS}
    taught = phase38_prereg.taught_anywhere()
    excluded_years = sorted(str(n) for n in range(1800, 2026) if str(n) in taught)
    assert excluded_years == ["1893", "1906", "1941", "1953", "1962", "1974", "1987"]
    assert len(houses) == 8768
    assert tuple(house_rej) == phase38_prereg.NUMERIC_FILTERS
    assert house_rej["substring_minted"] == 219
    assert house_rej["excluded"] == 13
    assert not set(houses) & set(years)
    with pytest.raises(SystemExit, match="NUMERIC_RANGES"):
        phase38_prereg.numeric_candidates("street", None, {}, (), accepted=[])


def test_neighbour_flags(numeric):
    assert phase38_prereg.neighbour_flags(["1987", "1988", "2000"]) == [False, True, False]
    years = numeric[0]
    flags = phase38_prereg.neighbour_flags(years)
    assert sum(flags) == 101


@pytest.fixture(scope="module")
def minted_all(tok, parsed):
    completions, questions = parsed
    return phase38_prereg.mint_all(tok, completions, questions, per_slot=24)


def test_mint_all_reads_the_seed_and_covers_every_slot(tok, parsed, minted_all, minted24, numeric):
    assert minted_all["seed"] == phase35_prereg.seed_list()[0] == 1337
    assert minted_all["per_slot"] == 24
    assert tuple(minted_all["slots"]) == phase38_prereg.SLOTS
    assert minted_all["stop_draw"] == minted24["stop_draw"]
    assert minted_all["stream"] == minted24["stream"]
    years, year_rej, houses, house_rej = numeric
    for slot in phase38_prereg.NAME_SLOTS:
        row = minted_all["slots"][slot]
        assert row["cleared"] == minted24["lists"][slot]
        assert row["rejections"] == minted24["rejections"][slot]
        assert "neighbour_d1" not in row
    for slot, kept, rej in (("birth_year", years, year_rej), ("house_number", houses, house_rej)):
        row = minted_all["slots"][slot]
        assert row["cleared"] == phase38_prereg.seeded_shuffle(kept, minted_all["seed"])
        assert row["rejections"] == rej
        flags = phase38_prereg.neighbour_flags(row["cleared"])
        assert row["neighbour_d1"] == [i for i, f in enumerate(flags) if f]
    for slot, row in minted_all["slots"].items():
        assert row["n_cleared"] == len(row["cleared"])
        assert row["max_set_size"] == phase38_prereg.max_set_size(row["n_cleared"])
        assert row["taught_token_count"] == len(
            tok.encode(next(f.value for f in phase14_factset.LOCKED_FACTS if f.slot == slot))
        )
    assert minted_all["slots"]["birth_year"]["max_set_size"] == 220
    assert len(minted_all["slots"]["birth_year"]["neighbour_d1"]) == 101


def test_mint_all_seed_is_read_not_typed(tok, parsed, minted_all, monkeypatch):
    completions, questions = parsed
    monkeypatch.setattr(phase35_prereg, "seed_list", lambda: (7, 8))
    other = phase38_prereg.mint_all(tok, completions, questions, per_slot=8)
    assert other["seed"] == 7
    for slot in phase38_prereg.NAME_SLOTS:
        assert other["slots"][slot]["cleared"] != minted_all["slots"][slot]["cleared"][:8]


def test_mint_all_stops_on_a_short_slot(tok, parsed):
    completions, questions = parsed
    with pytest.raises(SystemExit) as raised:
        phase38_prereg.mint_all(tok, completions, questions, per_slot=24, max_draws=50)
    message = str(raised.value)
    assert "D-26" in message
    for slot in phase38_prereg.NAME_SLOTS:
        assert slot in message


def test_minted_values_pass_the_phase17_filters(tok, parsed, minted_all):
    import phase17_persona_facts
    import phase17_personas  # torch at import: tests only

    _, questions = parsed
    values = [v for s in phase38_prereg.NAME_SLOTS for v in minted_all["slots"][s]["cleared"][:24]]
    values += [
        v for s in phase38_prereg.NUMERIC_RANGES for v in minted_all["slots"][s]["cleared"][:24]
    ]
    assert len(values) == len(set(values)) == 8 * 24
    assert phase17_personas.filter_roundtrip(tok, values) == tuple(values)
    phase17_personas.filter_substring_disjoint(values, phase17_persona_facts.FORBIDDEN_VALUES)
    phase17_personas.filter_absent_from_questions(values, _flat_questions(questions))
    phase17_personas.filter_token_budget({v: len(tok.encode(v)) for v in values})


def test_max_set_size_and_nested_sizes():
    assert phase38_prereg.max_set_size(2048) == 512
    assert phase38_prereg.max_set_size(219) == 220
    assert phase38_prereg.max_set_size(511) == 512
    assert phase38_prereg.nested_sizes(512) == (8, 32, 128, 512)
    assert phase38_prereg.nested_sizes(220) == (8, 32, 128, 220)
    assert phase38_prereg.nested_sizes(8) == (8,)
    with pytest.raises(SystemExit):
        phase38_prereg.nested_sizes(7)


_BANNED_RANDOM = {
    "choice",
    "choices",
    "shuffle",
    "sample",
    "randrange",
    "randint",
    "uniform",
    "getrandbits",
}
_RANDOM_CONSTRUCTORS = {"mint_names", "seeded_shuffle"}


def _random_failures(sources):
    """Pitfall 6: Random methods other than random() and random.Random outside the two owners."""
    failures, random_calls = [], 0
    for relpath, source in sources:
        tree = ast.parse(source)
        allowed = set()
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in _RANDOM_CONSTRUCTORS:
                allowed |= {id(n) for n in ast.walk(node)}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "random":
                failures.append(f"{relpath}:{node.lineno}: from random import")
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
                continue
            attr = node.func.attr
            if attr in _BANNED_RANDOM:
                failures.append(f"{relpath}:{node.lineno}: .{attr}(")
            elif attr == "random":
                random_calls += 1
            elif attr == "Random" and id(node) not in allowed:
                failures.append(
                    f"{relpath}:{node.lineno}: random.Random outside {_RANDOM_CONSTRUCTORS}"
                )
    return failures, random_calls


def test_only_random_is_called_in_phase38_scripts(tmp_path):
    paths = sorted(_SCRIPTS.glob("phase38_*.py"))
    assert paths, "meta-guard: no scripts/phase38_*.py"
    sources = [(p.relative_to(_ROOT).as_posix(), p.read_text(encoding="utf-8")) for p in paths]
    failures, random_calls = _random_failures(sources)
    assert failures == []
    assert random_calls > 0, "meta-guard: no .random() call found, the gate would be vacuous"
    source = (_ROOT / PREREG).read_text(encoding="utf-8")
    for name, plant in (
        ("choice.py", "\n\ndef planted(rng, x):\n    return rng.choice(x)\n"),
        ("ctor.py", "\n\nRNG = random.Random(0)\n"),
    ):
        planted = _planted(tmp_path, source, source + plant, name)
        assert _random_failures([(name, planted)])[0], name
