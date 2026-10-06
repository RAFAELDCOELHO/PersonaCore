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

import ast
import copy
import fnmatch
import functools
import inspect
import json
import math
import os
import pathlib
import statistics
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
import phase40_prereg  # noqa: E402  (same)

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
    assert repr(phase40_prereg.E2_STOP_HOURS) == "11.83638889157415"
    stop = phase36_prereg.ENTRIES["front_stop_factor"]["value"] * _budget()["front_hours"]["E2"]
    assert phase40_prereg.E2_STOP_HOURS == stop
    if phase40_prereg.D13_INCLUDED:
        assert repr(phase40_prereg.E2_PROJECTION_HOURS) == "7.9518624092864085"
        assert repr(phase40_prereg.E2_TOTAL_HOURS) == "77.78526798055215"
    else:
        assert repr(phase40_prereg.E2_PROJECTION_HOURS) == "7.890925927716101"
        assert repr(phase40_prereg.E2_TOTAL_HOURS) == "77.72433149898184"
    assert phase40_prereg.E2_PROJECTION_HOURS == _formula(
        phase40_prereg.D13_ADAPTERS, phase40_prereg.D13_NLLS_PER_ADAPTER
    )
    assert phase40_prereg.E2_PROJECTION_HOURS <= phase40_prereg.E2_STOP_HOURS


def _fsum_with(**fronts):
    return math.fsum({**_budget()["front_hours"], **fronts}.values())


def test_approval_record_total_with_e5_e6():
    if phase40_prereg.D13_INCLUDED:
        assert repr(phase40_prereg.E2_E5_E6_TOTAL_HOURS) == "78.12639556620314"
        assert repr(phase40_prereg.E2_E5_E6_TOTAL_HOURS_E6_ACTUAL_GATE) == "78.12556459250179"
    else:
        assert repr(phase40_prereg.E2_E5_E6_TOTAL_HOURS) == "78.06545908463283"
        assert repr(phase40_prereg.E2_E5_E6_TOTAL_HOURS_E6_ACTUAL_GATE) == "78.06462811093148"
    e5 = phase38_prereg.E5_PROJECTION_HOURS
    assert phase40_prereg.E2_E5_E6_TOTAL_HOURS == _fsum_with(
        E2=phase40_prereg.E2_PROJECTION_HOURS, E5=e5, E6=phase39_prereg.E6_PROJECTION_HOURS
    )
    assert phase40_prereg.E2_E5_E6_TOTAL_HOURS_E6_ACTUAL_GATE == _fsum_with(
        E2=phase40_prereg.E2_PROJECTION_HOURS,
        E5=e5,
        E6=phase39_prereg.E6_PROJECTION_HOURS_ACTUAL_GATE,
    )
    assert phase40_prereg.E2_TOTAL_HOURS == _fsum_with(E2=phase40_prereg.E2_PROJECTION_HOURS)
    block = phase40_prereg.approval_block()
    assert block["e2_e5_e6_total_hours"] == phase40_prereg.E2_E5_E6_TOTAL_HOURS
    assert (
        block["e2_e5_e6_total_hours_e6_actual_gate"]
        == phase40_prereg.E2_E5_E6_TOTAL_HOURS_E6_ACTUAL_GATE
    )
    assert block["committed_total_hours"] == _budget()["total_hours"]
    assert block["e2_total_hours"] == phase40_prereg.E2_TOTAL_HOURS
    assert block["e5_projection_hours"] == e5
    assert block["e6_projection_hours"] == phase39_prereg.E6_PROJECTION_HOURS
    assert (
        block["e6_projection_hours_actual_gate"] == phase39_prereg.E6_PROJECTION_HOURS_ACTUAL_GATE
    )


def test_approval_d13_nll_count_is_derived():
    count = phase40_prereg.d13_nlls_per_adapter()
    assert count == 512 + 8 + 27 * 8 + 27 * 7
    assert count == _d13_count()
    assert phase40_prereg.D13_NLLS_PER_ADAPTER == (count if phase40_prereg.D13_INCLUDED else 0)
    assert phase40_prereg.D13_ADAPTERS == (
        _budget()["unit_caps"]["E2"]["seeds"] if phase40_prereg.D13_INCLUDED else 0
    )
    assert type(phase40_prereg.D13_INCLUDED) is bool and type(phase40_prereg.D11_APPROVED) is bool


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

    budget = _budget()
    first = phase40_prereg.approval_block()
    second = phase40_prereg.approval_block()
    json.dumps(first)
    assert first == second and first is not second
    assert tuple(first) == _APPROVAL_KEYS == phase40_prereg.APPROVAL_KEYS
    assert first["ruling"] == phase40_prereg.APPROVALS_RULING
    assert first["r3_conditions"] == phase40_prereg.R3_CONDITIONS_RULING
    assert first["record_total_ruling"] == phase40_prereg.RECORD_TOTAL_RULING
    assert first["addendum_ruling"] == phase40_prereg.ADDENDUM_RULING
    assert first["d11_approved"] is phase40_prereg.D11_APPROVED
    assert first["d13_included"] is phase40_prereg.D13_INCLUDED
    assert first["d13_nlls_per_adapter"] == phase40_prereg.D13_NLLS_PER_ADAPTER
    assert first["d13_adapters"] == phase40_prereg.D13_ADAPTERS
    assert first["e2_projection_hours"] == phase40_prereg.E2_PROJECTION_HOURS
    assert first["committed_front_hours_e2"] == budget["front_hours"]["E2"]
    assert first["e2_stop_hours"] == phase40_prereg.E2_STOP_HOURS
    assert first["committed_unit_caps_e2"] == budget["unit_caps"]["E2"]
    assert first["budget_record"] == "results/phase36_budget.json" == phase40_prereg.BUDGET_RECORD
    assert first["untouched"] == [
        phase36_ledger.LEDGER_PATH,
        phase40_prereg.BUDGET_RECORD,
        "scripts/phase36_ledger.py",
        "scripts/phase36_caps.py",
    ]
    assert first["untouched"][0] == "ledger/v6_mps_ledger.jsonl"
    first["untouched"].clear()
    first["rulings"]["R-1"] = "planted"
    first["committed_unit_caps_e2"]["seeds"] = 0
    third = phase40_prereg.approval_block()
    assert third == second
    assert len(third["untouched"]) == 4
    assert third["committed_unit_caps_e2"] == budget["unit_caps"]["E2"]


def test_record_paths_from_the_registry():
    registry = phase35_prereg.SLOTS["e1_condition_c_band_inputs"]["input_records"][0]
    assert phase40_prereg.NOISE_FLOOR_RECORD == registry == "results/phase40_noise_floor.json"
    assert phase40_prereg.REPORT_RECORD == "results/phase40_noise_floor_report.md"
    assert phase40_prereg.RECORD_GLOB == "results/phase40_*"
    assert phase40_prereg.seed_record(1337) == "results/phase40_seed1337.json"
    assert phase40_prereg.a2_record("full", 1337) == "results/phase40_a2_full_seed1337.json"
    assert phase40_prereg.a2_record("m2", 2024) == "results/phase40_a2_m2_seed2024.json"
    assert phase40_prereg.run_id(1339) == "v6/40/E2/seed1339"
    assert phase40_prereg.GROUPS == ("full", "m2")
    seeds = phase35_prereg.seed_list()
    paths = [phase40_prereg.NOISE_FLOOR_RECORD, phase40_prereg.REPORT_RECORD]
    paths += [phase40_prereg.seed_record(s) for s in seeds]
    paths += [phase40_prereg.a2_record(g, s) for g in phase40_prereg.GROUPS for s in seeds]
    assert all(fnmatch.fnmatch(path, phase40_prereg.RECORD_GLOB) for path in paths)
    assert len(set(paths)) == len(paths)
    with pytest.raises(SystemExit, match=r"^\[phase40_prereg\]"):
        phase40_prereg.a2_record("planted", 1337)


# =================================================================================================
# (2) THE ENTRIES, BOTH FILLS AND SEEDS.
# =================================================================================================

_ENTRY_NAMES = {
    "e2_S",
    "e2_noise_floor_estimator",
    "fresh_training",
    "a2_pass",
    "run_order",
    "seed_outcomes",
    "determinism_check",
    "d08_correction",
    "d08b_residual",
    "d12_rereading",
    "d13_addition",
    "predictions",
    "approvals",
    "record_layout",
    "e2_projection_hours",
    "e2_total_hours",
    "e2_stop_hours",
}
_DERIVED = {"e2_S", "e2_projection_hours", "e2_total_hours", "e2_stop_hours"}


def test_e2_s_is_read_never_typed():
    read = _budget()["e2_seed_count"]
    assert phase40_prereg.E2_S == read == 5
    assert type(phase40_prereg.E2_S) is int
    assert phase40_prereg.BUDGET_RECORD in phase40_prereg.ENTRIES["e2_S"]["source"]
    assert phase40_prereg.ENTRIES["e2_S"]["value"] == read
    # NON-VACUITY: a derivation whose source omits the read path is refused by the fill.
    omitted = {**phase40_prereg.ENTRIES["e2_S"], "source": "35-CONTEXT Addendum to D-15"}
    with pytest.raises(SystemExit):
        phase35_prereg.fill(
            "e2_S", input_records=(phase40_prereg.BUDGET_RECORD,), derivation=omitted
        )


def test_seeds_are_the_seed_list_prefix():
    assert (
        phase40_prereg.SEEDS
        == phase35_prereg.seed_list()[: phase40_prereg.E2_S]
        == (1337, 2024, 1338, 2025, 1339)
    )
    assert phase40_prereg.SEEDS[:2] == phase35_prereg.e1_teaching_seeds()
    assert len(phase40_prereg.SEEDS) == _budget()["unit_caps"]["E2"]["seeds"]
    assert phase40_prereg.E2_S >= phase35_prereg.ENTRIES["e2_min_seeds"]["value"]


def test_fill_holds_both_estimators():
    filled = phase40_prereg.E2_NOISE_FLOOR_ESTIMATOR
    entry = phase40_prereg.ENTRIES["e2_noise_floor_estimator"]
    assert set(filled) == {"value", "derivation", "kind", "source"}
    for field in ("value", "derivation", "kind", "source"):
        assert filled[field] == entry[field], field
    assert filled["kind"] == "preference"
    value = filled["value"]
    assert set(value) == {"recall_floor", "gap_noise_floor"}
    assert value["recall_floor"]["groups"] == phase40_prereg.GROUPS
    with pytest.raises(TypeError):
        filled["kind"] = "derived"
    with pytest.raises(TypeError):
        value["recall_floor"]["published"] = "planted"
    for d_id in ("D-01", "D-02", "D-03", "D-04", "D-05", "D-09", "D-10", "D-16", "R-1", "R-2"):
        assert d_id in filled["derivation"], d_id


def _dict_value_constants(source, key):
    """The string constants keyed ``key`` in any dict literal of ``source`` (docstrings are never
    dict values, so they are excluded by construction)."""
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values, strict=True):
                if isinstance(k, ast.Constant) and k.value == key and isinstance(v, ast.Constant):
                    found.append(v.value)
    return found


def test_sampling_noise_and_crn_are_declared():
    source = (_ROOT / PREREG).read_text(encoding="utf-8")
    found = _dict_value_constants(source, "sampling_noise")
    assert len(found) == 1, "meta-guard: the sampling_noise constant was not found exactly once"
    text = found[0]
    assert "sampling noise" in text and "common random numbers" in text
    assert (
        text == phase40_prereg.E2_NOISE_FLOOR_ESTIMATOR["value"]["recall_floor"]["sampling_noise"]
    )


def test_entries_names_kinds_and_d_ids():
    kinds = {name: entry["kind"] for name, entry in phase40_prereg.ENTRIES.items()}
    assert set(kinds) == _ENTRY_NAMES
    assert len(kinds) == len(_ENTRY_NAMES) == 17
    assert {n for n, k in kinds.items() if k == "derived"} == _DERIVED
    for name, entry in phase40_prereg.ENTRIES.items():
        assert "D-" in entry["derivation"] or "P-" in entry["derivation"], name
    entries = phase40_prereg.ENTRIES
    assert entries["e2_projection_hours"]["value"] == phase40_prereg.E2_PROJECTION_HOURS
    assert entries["e2_total_hours"]["value"] == phase40_prereg.E2_TOTAL_HOURS
    assert entries["e2_stop_hours"]["value"] == phase40_prereg.E2_STOP_HOURS
    assert entries["d13_addition"]["value"]["included"] is phase40_prereg.D13_INCLUDED
    assert entries["determinism_check"]["value"]["criterion"] is False
    assert type(entries["determinism_check"]["value"]["pairs"]) is tuple
    with pytest.raises(TypeError):
        entries["planted"] = {}


# =================================================================================================
# (3) ANCESTRY (SC3, T-40-04): frozen before every results/phase40_* record. Honest at zero records
# and after them.
# =================================================================================================


def _strictly_before(x, y):
    run = subprocess.run(("git", "merge-base", "--is-ancestor", x, y), cwd=_ROOT, check=False)
    return x != y and run.returncode == 0


def _first_add(path):
    return _git("log", "--diff-filter=A", "--format=%H", "--", path).split()[-1]


def _phase40_records():
    return sorted(_git("ls-files", "results/phase40_*").split())


def test_phase40_prereg_is_frozen_before_every_phase40_record():
    _assert_frozen_before(PREREG, _phase40_records())
    # NON-VACUITY (natural RED): the v6.0 pre-registration was added before this one existed.
    with pytest.raises(subprocess.CalledProcessError):
        _assert_frozen_before(PREREG, ["scripts/phase35_prereg.py"])


def test_this_test_file_is_first_added_before_every_phase40_record():
    # Only the FIRST add: a later fix to this file must not redden the guard forever.
    mine = _first_add("tests/test_phase40_prereg.py")
    for record in _phase40_records():
        assert _strictly_before(mine, _first_add(record)), record
    # NON-VACUITY: the same check against a file added long before this one is False.
    assert not _strictly_before(mine, _first_add("scripts/phase35_prereg.py"))


def test_records_at_commit_is_true_at_the_first_commit():
    first = _git("log", "--format=%H", "--", PREREG).split()[-1]
    at_first = _git("ls-tree", "-r", "--name-only", first, "--", "results/").split()
    assert at_first, "meta-guard: the first commit's results/ tree is empty, the check is vacuous"
    assert not [path for path in at_first if path.startswith("results/phase40_")]
    assert phase40_prereg.RECORDS_AT_COMMIT == 0


def test_input_paths_resolve_from_the_registry():
    slots = phase35_prereg.SLOTS
    assert slots["e2_S"]["input_records"] == (phase40_prereg.BUDGET_RECORD,)
    assert slots["e2_noise_floor_estimator"]["input_records"] == ()
    assert phase40_prereg.RECORD_GLOB in phase35_prereg.V6_RESULT_PATHS
    budget = phase40_prereg.BUDGET_RECORD
    assert _git("ls-files", "--error-unmatch", budget) == budget


# =================================================================================================
# (4) RAFAEL'S RULINGS, QUOTED AT THEIR FIXED COMMITS (T-40-06, T-40-08).
# =================================================================================================

_CONTEXT_PATH = ".planning/phases/40-m2-seed-noise-floor/40-CONTEXT.md"
_LOG_PATH = ".planning/phases/40-m2-seed-noise-floor/40-DISCUSSION-LOG.md"
# The "Approvals commit" 03de080 of 40-01-SUMMARY.md: the commit that recorded Rafael's reply.
_APPROVALS_SHA = "03de0800e40825c7438b381c9bec4217466fc6ad"
_ADDENDUM_SHA = "544ed02"


def _lines_at(prefix, text):
    """The lines of ``text`` starting with ``prefix``."""
    return [line for line in text.splitlines() if line.startswith(prefix)]


def _quote(line):
    """The text between the line's first and last double quote."""
    return line[line.index('"') + 1 : line.rindex('"')]


def _approvals_text():
    return _git("show", f"{_APPROVALS_SHA}:{_CONTEXT_PATH}")


def _one_quote(prefix):
    lines = _lines_at(prefix, _approvals_text())
    assert len(lines) == 1, f"meta-guard: {len(lines)} lines start with {prefix!r}"
    quote = _quote(lines[0])
    assert len(quote.split()) >= 2, f"meta-guard: the {prefix!r} quote parsed too short"
    return quote


def test_approvals_ruling_is_quoted_verbatim():
    quote = _one_quote('- **Approvals reply (verbatim):** "')
    assert quote == phase40_prereg.APPROVALS_RULING
    assert quote in phase40_prereg.approval_block()["ruling"]
    assert quote in phase40_prereg.ENTRIES["approvals"]["derivation"]
    # The FIRST paragraph only, never the three-paragraph block of 40-01-SUMMARY.
    assert "\n" not in quote and quote.endswith("approved")
    for later in ("Condições", "No registro"):
        assert later not in phase40_prereg.APPROVALS_RULING, later
    d13 = _lines_at("- **D-13/D-14:** ", _approvals_text())
    assert len(d13) == 1, "meta-guard: the D-13/D-14 Approvals bullet is not one line"
    ruled = d13[0].split(":** ", 1)[1]
    assert ruled.startswith("approved") is phase40_prereg.D13_INCLUDED


def _option_ids(text):
    """{R-n: option id} of the four R bullets of ``text``: the first word after ':** '."""
    ids = {}
    for n in range(1, 5):
        lines = _lines_at(f"- **R-{n} (", text)
        assert len(lines) == 1, f"meta-guard: {len(lines)} R-{n} bullets"
        ids[f"R-{n}"] = lines[0].split(":** ", 1)[1].split()[0]
    return ids


def test_approvals_rulings_r1_to_r4_match_the_typed_values():
    text = _approvals_text()
    ids = _option_ids(text)
    assert len(ids) == 4, "meta-guard: four R bullets"
    rerun = "rerun-as-new-attempt" if phase40_prereg.DROPPED_SEED_RERUN else "never-rerun"
    typed = {
        "R-1": phase40_prereg.ADAPTER_OFF_RULE,
        "R-2": phase40_prereg.PRE_POST_RULE,
        "R-3": rerun,
        "R-4": phase40_prereg.A2_APPROVAL_RULE,
    }
    assert ids == typed
    assert phase40_prereg.approval_block()["rulings"] == ids
    # NON-VACUITY: a planted R-1 bullet with the other option fails the same comparison.
    line = _lines_at("- **R-1 (", text)[0]
    planted = text.replace(line, line.replace(":** mps-equality", ":** record-only", 1))
    assert planted != text, "meta-guard: the plant changed nothing"
    assert _option_ids(planted) != typed


def test_r3_conditions_and_record_total_are_quoted_verbatim():
    conditions = _one_quote('- **R-3 b conditions (verbatim):** "')
    total = _one_quote('- **Record total (verbatim):** "')
    block = phase40_prereg.approval_block()
    assert conditions == phase40_prereg.R3_CONDITIONS_RULING == block["r3_conditions"]
    assert conditions in phase40_prereg.ENTRIES["seed_outcomes"]["derivation"]
    assert total == phase40_prereg.RECORD_TOTAL_RULING == block["record_total_ruling"]
    assert total in phase40_prereg.ENTRIES["approvals"]["derivation"]
    # NON-VACUITY: one character changed fails the same equality.
    for quote in (conditions, total):
        changed = quote[:-1] + ("!" if quote[-1] != "!" else "?")
        assert changed not in (
            phase40_prereg.R3_CONDITIONS_RULING,
            phase40_prereg.RECORD_TOTAL_RULING,
        )


def test_addendum_ruling_is_quoted_verbatim():
    lines = _git("show", f"{_ADDENDUM_SHA}:{_LOG_PATH}").splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith('**Rafael (verbatim):** "')]
    assert len(starts) == 1, "meta-guard: the Addendum ruling line is not unique"
    bullet = [lines[starts[0]].strip()]
    for line in lines[starts[0] + 1 :]:
        if not line.strip():
            break
        bullet.append(line.strip())
    quote = _quote(" ".join(bullet))
    assert len(quote.split()) > 5, "meta-guard: the Addendum ruling parsed too short"
    assert quote == phase40_prereg.ADDENDUM_RULING
    assert "torch.equal" in quote
    assert phase40_prereg.approval_block()["addendum_ruling"] == quote


# =================================================================================================
# (5) NOTHING DERIVED IS TYPED (T-40-05).
# =================================================================================================


def test_no_derived_value_is_typed_in_the_prereg(tmp_path):
    import phase19_erasure as pin
    import phase19_floor

    budget = _budget()
    s = phase40_prereg.E2_S
    seeds = {s, pin.N_TARGET_QUESTIONS, math.comb(s, 2), s * s, _d13_count(), 512}
    adapter_off = _record("results/phase19_noise_floors.json")["dialogue_ppl_noise_floor"][
        "seed_a"
    ]["adapter_off"]
    floats = {
        phase40_prereg.E2_PROJECTION_HOURS,
        phase40_prereg.E2_TOTAL_HOURS,
        phase40_prereg.E2_STOP_HOURS,
        budget["front_hours"]["E2"],
        budget["total_hours"],
        phase40_prereg.E2_E5_E6_TOTAL_HOURS,
        phase40_prereg.E2_E5_E6_TOTAL_HOURS_E6_ACTUAL_GATE,
        phase38_prereg.E5_PROJECTION_HOURS,
        phase39_prereg.E6_PROJECTION_HOURS,
        phase39_prereg.E6_PROJECTION_HOURS_ACTUAL_GATE,
        phase19_floor.NONTARGET_NOISE_FLOOR,
        phase35_prereg.e1_condition_b_margin(),
        phase19_floor.DIALOGUE_PPL_NOISE_FLOOR,
        adapter_off,
    }
    assert repr(adapter_off) == "4.573349214207799", "meta-guard: not the committed adapter-off"
    assert all(type(f) is float for f in floats), "meta-guard: a census value is not a float"
    assert all(type(i) is int for i in seeds), "meta-guard: a census value is not an int"
    real = _ROOT / PREREG
    before = real.read_bytes()
    source = before.decode("utf-8")
    assert _literal_failures(source, seeds, floats, set()) == []
    plants = [
        ("stop.py", f"\nX = {phase40_prereg.E2_STOP_HOURS!r}\n"),
        ("s.py", f"\nS = {s!r}\n"),
    ]
    for name, line in plants:
        planted = _planted(tmp_path, source, source + line, name)
        assert _literal_failures(planted, seeds, floats, set()), name
    assert real.read_bytes() == before


# =================================================================================================
# (6) ENTRIES: EXACTLY FOUR FIELDS, NO PROPOSER; THE PRIVATE HELPERS; THE PLAN-TIME LABELS.
# =================================================================================================


def _good_entry():
    return {"value": 1, "derivation": "d", "kind": "derived", "source": "s"}


def test_entries_have_exactly_four_fields_and_no_proposer(tmp_path):
    assert phase40_prereg.ENTRY_FIELDS is phase35_prereg.ENTRY_FIELDS
    assert phase40_prereg.KINDS is phase35_prereg.KINDS
    for name, entry in phase40_prereg.ENTRIES.items():
        assert set(entry) == {"value", "derivation", "kind", "source"}, name
    assert phase40_prereg._prove_entries() is None

    phase40_prereg._prove_entry("ok", _good_entry())
    refused = (
        {**_good_entry(), "proposer": "Rafael"},
        {**_good_entry(), "adopted_by": "Rafael"},
        {k: v for k, v in _good_entry().items() if k != "source"},
        {**_good_entry(), "kind": "guess"},
        {**_good_entry(), "derivation": ""},
        {**_good_entry(), "value": phase40_prereg.FORBIDDEN_PHRASE},
        [1],
    )
    for entry in refused:
        with pytest.raises(SystemExit, match=r"^\[phase40_prereg\]"):
            phase40_prereg._prove_entry("x", entry)

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
        source, first.lineno, first.col_offset + 1, phase40_prereg.FORBIDDEN_PHRASE
    )
    ast.parse(planted_phrase)
    assert _entry_string_failures(_planted(tmp_path, source, planted_phrase, "phrase.py"))
    assert real.read_bytes() == before


def test_prove_count_and_read():
    with pytest.raises(SystemExit, match=r"^\[phase40_prereg\] x$"):
        phase40_prereg._prove(False, "x")
    assert phase40_prereg._prove(True, "x") is None
    assert phase40_prereg._prove_count("n", 0) is None
    for bad in (True, -1, 1.0):
        with pytest.raises(SystemExit, match=r"^\[phase40_prereg\]"):
            phase40_prereg._prove_count("n", bad)
    read = phase40_prereg._read(phase40_prereg.BUDGET_RECORD)
    assert isinstance(read, dict) and "unit_caps" in read


_LABEL = "default taken at plan time, not yet confirmed by Rafael"
# Keyed by ENTRY NAME: plan 04 moves each name to its confirmed form with a local edit.
# seed_outcomes is not here: R-3 was ruled at 40-01, and its derivation cites "R-3".
_UNCONFIRMED = {
    "e2_noise_floor_estimator": "D-04",
    "a2_pass": "NOISE-01",
    "run_order": "D-15",
    "record_layout": "D-15",
}


def test_preferences_are_labelled():
    entries = phase40_prereg.ENTRIES
    for name, d_id in _UNCONFIRMED.items():
        derivation = entries[name]["derivation"]
        assert d_id in derivation and _LABEL in derivation, name
    labelled = {name for name, entry in entries.items() if _LABEL in entry["derivation"]}
    assert labelled == set(_UNCONFIRMED)
    assert "seed_outcomes" not in _UNCONFIRMED
    assert "R-3" in entries["seed_outcomes"]["derivation"]


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
import phase40_prereg

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
    "e2_s": phase40_prereg.E2_S,
    "seeds": list(phase40_prereg.SEEDS),
    "planted": [os.fspath(p) for p in planted],
    "planted_flagged": list(_FLAGGED),
}}))
"""


def test_importing_the_prereg_opens_no_checkpoint(tmp_path):
    """This file loads torch through seed_list() by design; an "open" audit hook watches the
    import (now including the module-level phase38_prereg and phase39_prereg imports).

    Blind spot: safetensors opens files in Rust without a Python "open" audit event, so a
    safetensors read is invisible to the hook; the sys.modules leg covers it.
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
    assert result["e2_s"] == 5
    assert result["seeds"] == [1337, 2024, 1338, 2025, 1339]
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


def test_phase40_scripts_pass_the_slot_census():
    paths = sorted(_SCRIPTS.glob("phase40_*.py"))
    assert paths, "meta-guard: no scripts/phase40_*.py, the census would be vacuous"
    sources = [(p.relative_to(_ROOT).as_posix(), p.read_text(encoding="utf-8")) for p in paths]
    assert _slot_census_failures(sources) == []


def test_no_skips_in_this_file(tmp_path):
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert _skip_failures(source) == []
    planted = source + '\n\ndef test_planted():\n    pytest.skip("x")\n'
    assert _skip_failures(_planted(tmp_path, source, planted, "skip.py"))


def test_census_every_phase40_prereg_function_has_a_cpu_test(tmp_path):
    real = _ROOT / PREREG
    before = real.read_bytes()
    source = before.decode("utf-8")
    test_source = pathlib.Path(__file__).read_text(encoding="utf-8")
    defs = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)]
    assert defs, "meta-guard: the prereg defines no function, the census would be vacuous"
    assert _untested_functions("phase40_prereg", source, test_source) == []

    planted = source + '\n\ndef planted_untested():\n    """Planted."""\n'
    copied = _planted(tmp_path, source, planted, "untested.py")
    assert _untested_functions("phase40_prereg", copied, test_source) == ["planted_untested"]
    assert real.read_bytes() == before


# =================================================================================================
# (8) PLAN 40-03: THE PURE ESTIMATOR FUNCTIONS, ON COMMITTED v3.0 RECORDS AND TRUTH TABLES.
# =================================================================================================

_PHASE18 = "results/phase18_arm_adapter-on.json"
_REPLICATE = "results/phase19_arm_replicate.json"
_RETRAIN = "results/phase19_arm_retrain.json"


@functools.cache
def _committed_rows(rel):
    """Rows of a committed arm record, pooled with the M2 record's family and tiers (the Phase 18
    record carries every family and no attack_family: phase19_run.py:1715-1722)."""
    scope = phase40_prereg.a2_scope(_record(_RETRAIN))
    return phase40_prereg.a2_rows(_record(rel), *scope)


def _rows(counts, n_questions=None):
    """Synthetic rows in the pin's row shape: one fact per core slot, ``counts`` {slot: n}."""
    import phase19_erasure as pin

    q = pin.N_TARGET_QUESTIONS if n_questions is None else n_questions
    rows = {}
    for slot in (*pin.GATED_NONTARGET_SLOTS, pin.TARGET_SLOT):
        n = counts.get(slot, 0)
        rows[f"f_{slot}"] = {
            "slot": slot,
            "n_answerable": n,
            "n_questions": q,
            "per_tier": {},
            "rate": n / q,
        }
    return rows


def test_rows_denominator_on_the_committed_m2_record():
    import phase19_erasure as pin

    record = _record(_RETRAIN)
    family, tiers = phase40_prereg.a2_scope(record)
    assert (family, tiers) == ("A2", ("core_held_out", "core_taught"))
    rows = phase40_prereg.a2_rows(record, family, tiers)
    core = (*pin.GATED_NONTARGET_SLOTS, pin.TARGET_SLOT)
    by_slot = phase40_prereg.slot_rows(rows)
    assert tuple(by_slot) == core
    assert pin.N_TARGET_QUESTIONS == 27
    for slot, row in by_slot.items():
        assert row["n_questions"] == 27, slot
        assert row["per_tier"]["core_taught"]["n_questions"] == 14, slot
        assert row["per_tier"]["core_held_out"]["n_questions"] == 13, slot
        assert row["rate"] == row["n_answerable"] / row["n_questions"]
    counts = {slot: row["n_answerable"] for slot, row in by_slot.items()}
    assert counts == {
        "pet_name": 0,
        "house_number": 17,
        "hometown": 18,
        "birth_year": 18,
        "person_name": 26,
        "cat_name": 27,
        "sibling_name": 27,
        "street": 27,
    }
    assert by_slot["house_number"]["fact_id"] == "cand_house_7412"
    # NON-VACUITY: a single-tier denominator (14) is refused, and so is a missing slot.
    with pytest.raises(SystemExit, match=r"^\[phase40_prereg\]"):
        phase40_prereg.a2_rows(record, family, ("core_taught",))
    short = {k: v for k, v in rows.items() if v["slot"] != "street"}
    with pytest.raises(SystemExit, match=r"^\[phase40_prereg\]"):
        phase40_prereg.slot_rows(short)
    with pytest.raises(SystemExit, match=r"^\[phase40_prereg\]"):
        phase40_prereg.a2_scope({"config": {"attack_family": "A2"}, "draws": []})


def test_pair_reproduces_the_v3_sampling_floor():
    pair = phase40_prereg.pair_d(_committed_rows(_PHASE18), _committed_rows(_REPLICATE))
    assert pair == {
        "d": 0.14814814814814814,
        "deltas": (
            0.0,
            0.0,
            0.0,
            0.0,
            0.03703703703703698,
            0.11111111111111105,
            0.14814814814814814,
        ),
    }
    committed = _record("results/phase19_noise_floors.json")["nontarget_noise_floor"]["value"]
    assert pair["d"] == committed


def test_pair_reproduces_the_taught_to_m2_maximum():
    pair = phase40_prereg.pair_d(_committed_rows(_PHASE18), _committed_rows(_RETRAIN))
    assert pair == {
        "d": 0.2592592592592592,
        "deltas": (0.0, 0.0, 0.0, 0.0, 0.2592592592592592, 0.0, 0.11111111111111116),
    }


def test_group_floor_truth_table():
    import phase19_erasure as pin

    q = pin.N_TARGET_QUESTIONS
    a, b = _rows({}), _rows({"house_number": 1})
    two = phase40_prereg.group_floor({1337: a, 2024: b})
    assert two["n_seeds"] == 2 and two["seeds"] == [1337, 2024]
    assert two["n_pairs"] == math.comb(2, 2)
    assert two["floor"] == two["max"] == two["min"] == 1 / q
    assert two["pairs"] == [
        {"seeds": [1337, 2024], "d": 1 / q, "deltas": list(phase40_prereg.pair_d(a, b)["deltas"])}
    ]
    # Three seeds, d = 1/27, 4/27, 4/27: a tie at the max keeps both pairs.
    c = _rows({"street": 4})
    three = phase40_prereg.group_floor({1337: a, 2024: b, 1338: c})
    assert three["n_pairs"] == math.comb(3, 2)
    assert [p["seeds"] for p in three["pairs"]] == [[1337, 2024], [1337, 1338], [2024, 1338]]
    assert [p["d"] for p in three["pairs"]] == [1 / q, 4 / q, 4 / q]
    assert three["floor"] == statistics.fmean([1 / q, 4 / q, 4 / q])
    assert three["max"] == 4 / q and three["min"] == 1 / q
    # An identical pair: d = 0 is the min.
    same = phase40_prereg.group_floor({1337: a, 2024: a, 1338: b})
    assert [p["d"] for p in same["pairs"]] == [0.0, 1 / q, 1 / q]
    assert same["min"] == 0.0 and same["floor"] == statistics.fmean([0.0, 1 / q, 1 / q])
    # Below e2_min_seeds whole seeds: no floor.
    assert phase35_prereg.ENTRIES["e2_min_seeds"]["value"] == 2
    with pytest.raises(SystemExit, match="INSUFFICIENT_SEEDS"):
        phase40_prereg.group_floor({1337: a})
    with pytest.raises(SystemExit, match="INSUFFICIENT_SEEDS"):
        phase40_prereg._pairs([1337])
    assert phase40_prereg._pairs([1337, 2024, 1338]) == [(1337, 2024), (1337, 1338), (2024, 1338)]


def test_extras_per_slot_spread():
    import phase19_erasure as pin

    q = pin.N_TARGET_QUESTIONS
    rows = {
        1337: _rows({"house_number": 17, "hometown": 18}),
        2024: _rows({"house_number": 20, "hometown": 18}),
        1338: _rows({"house_number": 25, "hometown": 9}),
    }
    spread = phase40_prereg.per_slot_spread(rows)
    assert tuple(spread) == pin.GATED_NONTARGET_SLOTS
    house = spread["house_number"]
    assert house["rates"] == [17 / q, 20 / q, 25 / q]
    assert house["counts"] == [[17, q], [20, q], [25, q]]
    assert house["range"] == 25 / q - 17 / q
    assert house["sd_sample"] == statistics.stdev(house["rates"])
    assert house["sd_population"] == statistics.pstdev(house["rates"])
    assert house["sd_sample"] != house["sd_population"]
    assert spread["street"]["range"] == 0.0 and spread["street"]["sd_sample"] == 0.0
    two = phase40_prereg.per_slot_spread({1337: rows[1337], 2024: rows[2024]})
    assert two["house_number"]["sd_sample"] == statistics.stdev([17 / q, 20 / q])
    assert phase40_prereg.group_floor(rows)["per_slot"] == spread


def _function_node(source, name):
    tree = ast.parse(source)
    found = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
    assert len(found) == 1, f"meta-guard: {len(found)} defs named {name}"
    return found[0]


def _pair_d_call_failures(source):
    """The pair_d AST gate: it calls pin.nontarget_noise_floor and pin.nontarget_deltas, and never
    the builtin max (docstring excluded)."""
    node = _function_node(source, "pair_d")
    body = node.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]
    calls = [n for stmt in body for n in ast.walk(stmt) if isinstance(n, ast.Call)]
    assert calls, "meta-guard: pair_d holds no Call, the gate would be vacuous"
    pin_calls = {
        c.func.attr
        for c in calls
        if isinstance(c.func, ast.Attribute)
        and isinstance(c.func.value, ast.Name)
        and c.func.value.id == "pin"
    }
    failures = [
        f"pair_d never calls pin.{name}"
        for name in ("nontarget_noise_floor", "nontarget_deltas")
        if name not in pin_calls
    ]
    failures += [
        f"pair_d calls the builtin max at line {c.lineno}"
        for c in calls
        if isinstance(c.func, ast.Name) and c.func.id == "max"
    ]
    return failures


def test_pair_d_calls_the_pin_ast():
    source = (_ROOT / PREREG).read_text(encoding="utf-8")
    assert _pair_d_call_failures(source) == []
    # NON-VACUITY: a pair_d that returns max(deltas) fails the same check.
    node = _function_node(source, "pair_d")
    lines = source.splitlines()
    planted_def = [
        "def pair_d(rows_i, rows_j):",
        "    deltas = [abs(rows_i[k]['rate'] - rows_j[k]['rate']) for k in rows_i]",
        "    return {'d': max(deltas), 'deltas': tuple(deltas)}",
    ]
    planted = "\n".join(lines[: node.lineno - 1] + planted_def + lines[node.end_lineno :])
    ast.parse(planted)
    failures = _pair_d_call_failures(planted)
    assert any("nontarget_noise_floor" in f for f in failures)
    assert any("builtin max" in f for f in failures)


def test_recall_floor_publishes_the_larger_group_beside_v3():
    import phase19_floor

    full = {1337: _rows({}), 2024: _rows({"house_number": 1})}
    m2 = {1337: _rows({}), 2024: _rows({"hometown": 3})}
    floor = phase40_prereg.recall_floor(full, m2)
    assert floor["full"] == phase40_prereg.group_floor(full)
    assert floor["m2"] == phase40_prereg.group_floor(m2)
    assert floor["published"] == {"value": floor["m2"]["floor"], "group": "m2", "tie": False}
    assert floor["beside"] == {
        "sampling_floor": phase19_floor.NONTARGET_NOISE_FLOOR,
        "margin_at_gate": phase35_prereg.e1_condition_b_margin(),
        "margin_amended": False,
    }
    assert floor["estimator"] == "e2_noise_floor_estimator (preference)"
    flipped = phase40_prereg.recall_floor(m2, full)
    assert flipped["published"]["group"] == "full"
    assert flipped["published"]["value"] == floor["m2"]["floor"]
    tie = phase40_prereg.recall_floor(full, full)
    assert tie["published"] == {"value": tie["full"]["floor"], "group": "full", "tie": True}
    with pytest.raises(SystemExit, match=r"^\[phase40_prereg\]"):
        phase40_prereg.recall_floor(full, {1337: _rows({}), 1338: _rows({})})


# The CPU adapter-off reading with MPS hidden (B1, orchestrator 2026-10-05), typed in the TEST only.
_CPU_ADAPTER_OFF = 4.573348505014267
_COMMITTED_ON = 6.007920892362744
_COMMITTED_OFF = 4.573349214207799


def _with_off(record, off):
    planted = copy.deepcopy(record)
    for reading in (planted["dialogue_ppl"], planted["pre_erasure"]["dialogue_ppl"]):
        reading["adapter_off"] = off
    return planted


def test_gap_on_the_committed_m2_record(monkeypatch):
    committed = phase40_prereg.committed_adapter_off()
    assert committed == _COMMITTED_OFF
    record = _record(_RETRAIN)
    for rule in phase40_prereg.ADAPTER_OFF_RULES:
        monkeypatch.setattr(phase40_prereg, "ADAPTER_OFF_RULE", rule)
        gap = phase40_prereg.dialogue_gap(record, committed, device="mps")
        assert gap["gap"] == _COMMITTED_ON - _COMMITTED_OFF
        assert gap["adapter_on"] == _COMMITTED_ON and gap["adapter_off"] == _COMMITTED_OFF
        assert gap["adapter_off_matches_committed"] is True
        assert gap["rehearsal"] is False and gap["pre_post_equal"] is True
        assert gap["pre_post_abs_difference"] == {"adapter_on": 0.0, "adapter_off": 0.0}
        assert gap["rules"] == {"R-1": rule, "R-2": phase40_prereg.PRE_POST_RULE}
        assert gap["device"] == "mps" and gap["criterion"] is False
    planted = copy.deepcopy(record)
    planted["pre_erasure"]["dialogue_ppl"]["n_targets"] += 1
    with pytest.raises(SystemExit, match=r"^\[phase40_prereg\]"):
        phase40_prereg.dialogue_gap(planted, committed, device="mps")
    with pytest.raises(SystemExit, match=r"^\[phase40_prereg\]"):
        phase40_prereg.dialogue_gap(record, committed, device="")


def test_gap_device_scoped_adapter_off_truth_table(monkeypatch):
    committed = phase40_prereg.committed_adapter_off()
    record = _record(_RETRAIN)
    cpu = _with_off(record, _CPU_ADAPTER_OFF)
    assert _CPU_ADAPTER_OFF != committed, "meta-guard: the CPU reading equals the committed one"
    for rule in phase40_prereg.ADAPTER_OFF_RULES:
        monkeypatch.setattr(phase40_prereg, "ADAPTER_OFF_RULE", rule)
        gap = phase40_prereg.dialogue_gap(cpu, committed, device="cpu")
        assert gap["gap"] == _COMMITTED_ON - _CPU_ADAPTER_OFF
        assert gap["adapter_off_matches_committed"] is False and gap["rehearsal"] is True
        own = phase40_prereg.dialogue_gap(record, committed, device="cpu")
        assert own["adapter_off_matches_committed"] is True and own["rehearsal"] is True
    monkeypatch.setattr(phase40_prereg, "ADAPTER_OFF_RULE", "mps-equality")
    with pytest.raises(SystemExit, match="R-1"):
        phase40_prereg.dialogue_gap(cpu, committed, device="mps")
    monkeypatch.setattr(phase40_prereg, "ADAPTER_OFF_RULE", "record-only")
    gap = phase40_prereg.dialogue_gap(cpu, committed, device="mps")
    assert gap["adapter_off_matches_committed"] is False and gap["rehearsal"] is False
    assert gap["committed_adapter_off"] == committed


def test_gap_pre_post_rule_truth_table(monkeypatch):
    committed = phase40_prereg.committed_adapter_off()
    record = _record(_RETRAIN)
    planted = copy.deepcopy(record)
    pre = planted["pre_erasure"]["dialogue_ppl"]
    pre["adapter_on"] += 0.5
    post = planted["dialogue_ppl"]
    monkeypatch.setattr(phase40_prereg, "PRE_POST_RULE", "post")
    gap = phase40_prereg.dialogue_gap(planted, committed, device="mps")
    assert gap["gap"] == post["adapter_on"] - post["adapter_off"]
    assert gap["pre_post_equal"] is False
    assert gap["pre_post_abs_difference"]["adapter_on"] > 0
    assert gap["pre_post_abs_difference"]["adapter_off"] == 0.0
    monkeypatch.setattr(phase40_prereg, "PRE_POST_RULE", "mean")
    gap = phase40_prereg.dialogue_gap(planted, committed, device="mps")
    on = statistics.fmean([pre["adapter_on"], post["adapter_on"]])
    off = statistics.fmean([pre["adapter_off"], post["adapter_off"]])
    assert gap["gap"] == on - off and gap["rules"]["R-2"] == "mean"
    monkeypatch.setattr(phase40_prereg, "PRE_POST_RULE", "refuse")
    with pytest.raises(SystemExit, match="R-2"):
        phase40_prereg.dialogue_gap(planted, committed, device="mps")
    for rule in phase40_prereg.PRE_POST_RULES:
        monkeypatch.setattr(phase40_prereg, "PRE_POST_RULE", rule)
        gap = phase40_prereg.dialogue_gap(record, committed, device="mps")
        assert gap["gap"] == _COMMITTED_ON - _COMMITTED_OFF and gap["pre_post_equal"] is True


def test_gap_noise_floor_truth_table():
    import phase19_floor

    two = phase40_prereg.gap_noise_floor({1337: 1.0, 2024: 1.25})
    assert two["value"] == two["max"] == abs(1.0 - 1.25)
    assert two["n_pairs"] == math.comb(2, 2)
    assert two["pairs"] == [{"seeds": [1337, 2024], "abs_gap_difference": 0.25}]
    assert two["gaps"] == {1337: 1.0, 2024: 1.25}
    assert two["beside"] == phase19_floor.DIALOGUE_PPL_NOISE_FLOOR
    three = phase40_prereg.gap_noise_floor({1337: 1.0, 2024: 1.25, 1338: 2.0})
    assert three["n_pairs"] == math.comb(3, 2)
    assert [p["abs_gap_difference"] for p in three["pairs"]] == [0.25, 1.0, 0.75]
    assert three["value"] == statistics.fmean([0.25, 1.0, 0.75]) and three["max"] == 1.0
    assert math.isfinite(three["value"]) and three["value"] >= 0
    # The committed v3.0 pair reproduces the D-07 gap prediction's reference.
    block = _record("results/phase19_noise_floors.json")["dialogue_ppl_noise_floor"]
    gaps = {
        block[k]["seed"]: block[k]["adapter_on"] - block[k]["adapter_off"]
        for k in ("seed_a", "seed_b")
    }
    assert phase40_prereg.gap_noise_floor(gaps)["value"] == phase19_floor.DIALOGUE_PPL_NOISE_FLOOR
    for bad in (math.inf, math.nan):
        with pytest.raises(SystemExit, match=r"^\[phase40_prereg\]"):
            phase40_prereg.gap_noise_floor({1337: 1.0, 2024: bad})
    with pytest.raises(SystemExit, match="INSUFFICIENT_SEEDS"):
        phase40_prereg.gap_noise_floor({1337: 1.0})


def test_d12_table_shape_and_signs():
    import phase19_erasure as pin

    v3 = phase40_prereg.v3_delta_taught_to_m2()
    retained = _record("results/phase19_retrain_scores.json")["retrain_scores"]["retained"]
    assert v3 == {row["slot"]: row["delta_taught_to_m2"] for row in retained.values()}
    assert set(v3) == set(pin.GATED_NONTARGET_SLOTS)
    full = {1337: _committed_rows(_PHASE18), 2024: _committed_rows(_REPLICATE)}
    m2 = {1337: _committed_rows(_RETRAIN), 2024: _committed_rows(_RETRAIN)}
    table = phase40_prereg.d12_table(full, m2)
    assert table["criterion"] is False
    assert tuple(table["per_slot"]) == pin.GATED_NONTARGET_SLOTS
    for slot, entry in table["per_slot"].items():
        assert entry["v3_delta_taught_to_m2"] == v3[slot]
        pairs = entry["pairs"]
        assert len(pairs) == len(full) * len(m2)
        assert sum(p["same_seed"] for p in pairs) == len(full)
        assert [(p["full_seed"], p["m2_seed"]) for p in pairs] == [
            (1337, 1337),
            (1337, 2024),
            (2024, 1337),
            (2024, 2024),
        ]
        for p in pairs:
            m2_rate = phase40_prereg.slot_rows(m2[p["m2_seed"]])[slot]["rate"]
            full_rate = phase40_prereg.slot_rows(full[p["full_seed"]])[slot]["rate"]
            assert p["m2_minus_full"] == m2_rate - full_rate
        assert pairs[0]["m2_minus_full"] == v3[slot], slot
    same = {slot: e["pairs"][0]["m2_minus_full"] for slot, e in table["per_slot"].items()}
    assert same == {
        "cat_name": 0.0,
        "street": 0.0,
        "sibling_name": 0.0,
        "person_name": 0.0,
        "house_number": -0.2592592592592592,
        "birth_year": 0.0,
        "hometown": -0.11111111111111116,
    }


_SAME_SEED_LABEL = "ruído de re-execução com a mesma semente (same-seed re-run noise)"


def test_d07_reading_labels():
    import phase19_erasure as pin

    q = pin.N_TARGET_QUESTIONS
    rows = _rows({"house_number": 17})
    same = phase40_prereg.d07_reading(True, rows, rows)
    assert same["tensor_identical"] is True and same["label"] is None
    assert same["criterion"] is False
    assert {c["delta"] for c in same["counts"].values()} == {0}
    assert tuple(same["counts"]) == (*pin.GATED_NONTARGET_SLOTS, pin.TARGET_SLOT)
    moved = phase40_prereg.d07_reading(False, _rows({"house_number": 19}), rows)
    assert moved["label"] == _SAME_SEED_LABEL
    assert moved["counts"]["house_number"] == {"new": [19, q], "committed": [17, q], "delta": 2}
    assert moved["counts"]["street"]["delta"] == 0
    assert phase40_prereg.count_deltas(rows, rows) == same["counts"]
    with pytest.raises(SystemExit, match=r"^\[phase40_prereg\]"):
        phase40_prereg.count_deltas(rows, _rows({}, n_questions=q + 1))


def test_d08b_truth_table():
    import phase19_erasure as pin

    q = pin.N_TARGET_QUESTIONS
    rows = _rows({"house_number": 17})
    assert phase40_prereg.D08B_OUTCOMES == ("NO_RESIDUAL", "V3_LIMITATION", "NOT_SEPARABLE")
    equal = phase40_prereg.d08b_reading(True, rows, rows)
    assert equal["outcome"] == "NO_RESIDUAL" and equal["max_abs_rate_difference"] == 0.0
    differ = _rows({"house_number": 20})
    limited = phase40_prereg.d08b_reading(True, rows, differ)
    assert limited["outcome"] == "V3_LIMITATION"
    assert limited["counts"]["house_number"]["delta"] == 3
    assert limited["max_abs_rate_difference"] == 3 / q
    assert limited["criterion"] is False
    for full in (rows, differ):
        apart = phase40_prereg.d08b_reading(False, rows, full)
        assert apart["outcome"] == "NOT_SEPARABLE"
    assert phase40_prereg.d08b_reading(False, rows, differ)["max_abs_rate_difference"] == 3 / q
    committed = _committed_rows(_PHASE18)
    assert phase40_prereg.d08b_reading(True, committed, committed)["outcome"] == "NO_RESIDUAL"


def _ledger_line(event, seed, utc, record=None):
    return {
        "utc": utc,
        "event": event,
        "run_id": phase40_prereg.run_id(seed),
        "phase": 40,
        "front": "E2",
        "record": record,
        "seconds": None,
        "flag": None,
        "stop": None,
        "ruling": None,
    }


def _ledger_lines():
    seed_record = phase40_prereg.seed_record
    return [
        _ledger_line("start", 1337, "t1"),
        _ledger_line("end", 1337, "t2", seed_record(1337)),
        _ledger_line("start", 2024, "t3"),
        _ledger_line("lost", 2024, "t4"),
        _ledger_line("start", 2025, "t5"),
        _ledger_line("lost", 2025, "t6"),
        _ledger_line("start", 2025, "t7"),
        _ledger_line("end", 2025, "t8", seed_record(2025)),
    ]


def test_seed_outcomes_whole_dropped_not_run(monkeypatch):
    seeds = phase40_prereg.SEEDS
    outcomes = phase40_prereg.seed_outcomes(_ledger_lines(), seeds)
    assert outcomes == {
        1337: "whole",
        2024: "dropped",
        1338: "not_run",
        2025: "whole",
        1339: "not_run",
    }
    assert tuple(outcomes) == seeds
    other = _ledger_lines()
    other[1] = _ledger_line("end", 1337, "t2", phase40_prereg.seed_record(2024))
    with pytest.raises(SystemExit, match=r"^\[phase40_prereg\]"):
        phase40_prereg.seed_outcomes(other, seeds)
    opened = [*_ledger_lines(), _ledger_line("start", 1338, "t9")]
    with pytest.raises(SystemExit, match="reconcile"):
        phase40_prereg.seed_outcomes(opened, seeds)
    # WR-01 (R-3 b "nunca para semente concluída"): any attempt after a whole one is refused.
    whole = [
        _ledger_line("start", 1337, "t1"),
        _ledger_line("end", 1337, "t2", phase40_prereg.seed_record(1337)),
    ]
    for close in (
        _ledger_line("lost", 1337, "t4"),
        _ledger_line("end", 1337, "t4", phase40_prereg.seed_record(1337)),
    ):
        with pytest.raises(SystemExit, match="R-3 b"):
            phase40_prereg.seed_outcomes([*whole, _ledger_line("start", 1337, "t3"), close], seeds)
    monkeypatch.setattr(phase40_prereg, "DROPPED_SEED_RERUN", False)
    assert phase40_prereg.pending_seeds(outcomes) == (1338, 1339)
    assert phase40_prereg.pending_seeds(outcomes, rerun=frozenset({2024})) == (1338, 1339)
    monkeypatch.setattr(phase40_prereg, "DROPPED_SEED_RERUN", True)
    assert phase40_prereg.pending_seeds(outcomes) == (1338, 1339)
    assert phase40_prereg.pending_seeds(outcomes, rerun=frozenset({2024})) == (2024, 1338, 1339)
    for bad in (frozenset({1337}), frozenset({1338})):
        with pytest.raises(SystemExit, match="R-3 b"):
            phase40_prereg.pending_seeds(outcomes, rerun=bad)


def test_seed_outcomes_lost_attempts_and_dropped_dir():
    lines = [
        _ledger_line("start", 2025, "s1"),
        _ledger_line("lost", 2025, "A"),
        _ledger_line("start", 1337, "s2"),
        _ledger_line("end", 1337, "s3", phase40_prereg.seed_record(1337)),
        _ledger_line("start", 2025, "s4"),
        _ledger_line("lost", 2025, "B"),
        _ledger_line("start", 2025, "s5"),
        _ledger_line("end", 2025, "s6", phase40_prereg.seed_record(2025)),
    ]
    assert phase40_prereg.lost_attempts(lines, 2025) == ["A", "B"]
    assert phase40_prereg.lost_attempts(lines, 1337) == []
    assert phase40_prereg.lost_attempts(lines, 1338) == []
    path = phase40_prereg.dropped_attempt_dir(2024, "2026-10-06T01:02:03.000004+00:00")
    assert path == "data/phase40_dropped/v6_40_E2_seed2024_2026-10-06T010203.000004+0000"
    assert ":" not in path and not fnmatch.fnmatch(path, phase40_prereg.RECORD_GLOB)
    assert phase40_prereg.DROPPED_ROOT == "data/phase40_dropped"
    assert phase40_prereg.DROPPED_MANIFEST == "manifest.json"
    with pytest.raises(SystemExit, match=r"^\[phase40_prereg\]"):
        phase40_prereg.dropped_attempt_dir(9999, "A")
    with pytest.raises(SystemExit, match=r"^\[phase40_prereg\]"):
        phase40_prereg.dropped_attempt_dir(2024, "")


_U = "2026-10-06T01:02:03.000004+00:00"


def _manifest(**changes):
    manifest = {
        "seed": 2024,
        "run_id": phase40_prereg.run_id(2024),
        "lost_utc": _U,
        "cause_note": "x",
        "approved": "approved",
        "head_at_dropped_attempt": "H",
        "relaunch_git_sha": "H",
        "head_change_declared": None,
        "kept": [
            {
                "from": "checkpoints/a.pt",
                "path": phase40_prereg.dropped_attempt_dir(2024, _U) + "/checkpoints/a.pt",
                "sha256": "0" * 64,
            }
        ],
    }
    manifest.update(changes)
    return manifest


def _manifest_failures(manifest):
    return phase40_prereg.dropped_manifest_failures(manifest, seed=2024, lost_utc=_U)


def test_seed_outcomes_dropped_manifest_truth_table():
    assert phase40_prereg._text(" x ") is True
    assert [phase40_prereg._text(v) for v in ("", "  ", None, 1)] == [False] * 4
    assert tuple(_manifest()) == phase40_prereg.DROPPED_MANIFEST_KEYS
    assert _manifest_failures(_manifest()) == []
    assert _manifest_failures(_manifest(kept=[])) == []
    assert _manifest_failures(_manifest(relaunch_git_sha="H2", head_change_declared="y")) == []
    item = _manifest()["kept"][0]
    missing = _manifest()
    del missing["cause_note"]
    plants = [
        ("cause_note", missing),
        ("planted", _manifest(planted=1)),
        ("seed", _manifest(seed=1337)),
        ("run_id", _manifest(run_id=phase40_prereg.run_id(1337))),
        ("lost_utc", _manifest(lost_utc="2026-10-06T09:09:09+00:00")),
        ("cause_note", _manifest(cause_note="")),
        ("cause_note", _manifest(cause_note="   ")),
        ("approved", _manifest(approved="ok")),
        ("relaunch_git_sha", _manifest(relaunch_git_sha="")),
        ("head_change_declared", _manifest(relaunch_git_sha="H2")),
        ("head_change_declared", _manifest(head_change_declared="y")),
        ("kept", _manifest(kept=[{**item, "path": "data/elsewhere/a.pt"}])),
        ("sha256", _manifest(kept=[{k: v for k, v in item.items() if k != "sha256"}])),
        ("extra", _manifest(kept=[{**item, "extra": 1}])),
    ]
    for key, manifest in plants:
        failures = _manifest_failures(manifest)
        assert failures, key
        assert any(key in failure for failure in failures), (key, failures)


def test_seed_outcomes_relaunch_head_truth_table():
    assert phase40_prereg.relaunch_declaration_name("h2") == "relaunch_h2.json"
    with pytest.raises(SystemExit, match=r"^\[phase40_prereg\]"):
        phase40_prereg.relaunch_declaration_name("")
    manifest = _manifest()
    assert phase40_prereg.latest_head_failures(manifest, None, launch_git_sha="H") == []
    moved = phase40_prereg.latest_head_failures(manifest, None, launch_git_sha="H2")
    assert len(moved) == 1 and "HEAD moved" in moved[0]
    declaration = {"launch_git_sha": "H2", "head_change_declared": "y", "approved": "approved"}
    assert tuple(declaration) == phase40_prereg.RELAUNCH_DECLARATION_KEYS
    assert phase40_prereg.latest_head_failures(manifest, declaration, launch_git_sha="H2") == []
    assert phase40_prereg.relaunch_declaration_failures(declaration, relaunch_git_sha="H") == []
    missing = dict(declaration)
    del missing["approved"]
    plants = [
        ("approved", missing),
        ("planted", {**declaration, "planted": 1}),
        ("launch_git_sha", {**declaration, "launch_git_sha": "H"}),
        ("head_change_declared", {**declaration, "head_change_declared": " "}),
        ("approved", {**declaration, "approved": "ok"}),
    ]
    for key, planted in plants:
        failures = phase40_prereg.relaunch_declaration_failures(planted, relaunch_git_sha="H")
        assert failures and any(key in f for f in failures), (key, failures)
    other = phase40_prereg.latest_head_failures(manifest, declaration, launch_git_sha="H3")
    assert other and any("launch_git_sha" in f for f in other)


def test_d13_block_reduction(monkeypatch):
    monkeypatch.setattr(phase40_prereg, "D13_INCLUDED", True)
    curve = {"8": 3, "32": 4}
    block = phase40_prereg.d13_block(
        curve=curve, gate_rank=2, a2_rank=2, committed_ranks=[1, 1, 3], minted_ranks=[2, 1]
    )
    assert block["anchor_curve"] == curve
    assert block["anchor_gate"] == {"rank": 2, "a2_record_rank": 2, "equal": True}
    assert block["r_q"]["committed"] == {
        "ranks": [1, 1, 3],
        "n1": phase39_prereg.n1([1, 1, 3]),
        "n": 3,
    }
    assert block["r_q"]["committed"]["n1"] == 2
    assert block["r_q"]["minted"] == {"ranks": [2, 1], "n1": 1, "n": 2}
    assert block["criterion"] is False
    unequal = phase40_prereg.d13_block(
        curve=curve, gate_rank=2, a2_rank=3, committed_ranks=[], minted_ranks=[]
    )
    assert unequal["anchor_gate"]["equal"] is False
    monkeypatch.setattr(phase40_prereg, "D13_INCLUDED", False)
    with pytest.raises(SystemExit, match="D-13"):
        phase40_prereg.d13_block(
            curve=curve, gate_rank=2, a2_rank=2, committed_ranks=[], minted_ranks=[]
        )
