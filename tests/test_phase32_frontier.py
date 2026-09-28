"""Plan 32-03: the v5.0 frontier assembler (AFRONT-02, AFRONT-03).

CPU-only. Every record here is FORGED from the committed v4.0 frontier (read as the HEAD blob),
re-keyed to the advr keys. Nothing is written under the real results/.
"""

import ast
import copy
import functools
import json
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

import mitigation_gate  # noqa: E402  (scripts/ is not a package)
import phase25_record  # noqa: E402  (same)
import phase25_verdict  # noqa: E402  (same)
import phase29_prereg  # noqa: E402  (same)
import phase30_points  # noqa: E402  (same)
import phase32_frontier as fr  # noqa: E402  (same)

from test_phase25_driver import (  # noqa: E402
    _git_argv_subcommands,
    _git_surface_failure,
    _scratch_repo,
)
from test_phase29_prereg import (  # noqa: E402
    _assert_frozen_before,
    _gate_retype_failures,
    _git,
    _planted,
)
from test_phase30_points import _wr05_failures  # noqa: E402

MODULE = _SCRIPTS / "phase32_frontier.py"
P = phase29_prereg
KEYS = P.POINT_KEYS()
REFUSAL = "REFUSED by the sanctioned route before the pin was reached"
READ_ONLY_GIT = {"ls-files", "show", "rev-parse", "status", "log", "merge-base"}

# The record-contract fields a forged v5 record copies off its v4.0 twin.
CONTRACT = (
    "taught_recall",
    "heldout_recall",
    "condition_c",
    "per_family_counts",
    "zero_extraction_has_nll",
    "draws_per_question",
    "draws_per_question_source",
    "adapter_sha256",
)


@pytest.fixture(autouse=True)
def clean_tree(monkeypatch):
    """emit refuses a dirty tree and this suite runs on dirty trees, so the guard is RECORDED."""
    calls = []
    monkeypatch.setattr(fr, "refuse_if_dirty", lambda **kw: calls.append(kw) or "")
    return calls


@functools.lru_cache(maxsize=None)
def _v4_bytes():
    return subprocess.run(
        ["git", "show", f"HEAD:{fr.V4_FRONTIER_PATH}"], cwd=_ROOT, capture_output=True, check=True
    ).stdout


@functools.lru_cache(maxsize=None)
def _v4():
    """The committed v4.0 frontier, parsed once. Never mutated by a test (the forge deep-copies)."""
    return json.loads(_v4_bytes())


def _v4_sha():
    import hashlib

    return hashlib.sha256(_v4_bytes()).hexdigest()


def _twin(leg):
    return P._V4_TWIN[f"advr_{leg}"]


def _v4_control_counts(twin):
    return _v4()["verdicts"]["control_readings"][twin]["recall_counts"]


# learnable = the v4 adv_n8 control's counts; unlearnable = the v4 adv_n64 control's.
def _counts(state):
    return _v4_control_counts({"learnable": "adv_n8", "unlearnable": "adv_n64"}[state])


def _set_counts(record, counts):
    for side in ("taught", "heldout"):
        k, n = counts[side]
        record[f"{side}_recall"] = dict(record[f"{side}_recall"], numerator=k, denominator=n)


def _recipe(leg):
    n = int(leg.removeprefix("n"))
    return {
        "replay_windows": P.replay_windows(n),
        "n_facts": n,
        "seed": P.DESIGNATED_SEED,
        "max_steps": P.MAX_STEPS,
    }


def _forged_records(n8="learnable", n64="unlearnable"):
    v4 = _v4()
    out = {}
    for leg, state in (("n8", n8), ("n64", n64)):
        twin = _twin(leg)
        for ratio in P.RATIO_GRID:
            key = P.point_key(f"advr_{leg}", ratio)
            is_control = key == P.control_key(leg)
            if state == "unlearnable" and not is_control:
                taught, heldout = (tuple(_counts(state)[s]) for s in ("taught", "heldout"))
                out[key] = P.refused_record(
                    key, taught=taught, heldout=heldout, recipe=_recipe(leg)
                )
                continue
            source = v4["points"][phase25_record.point_key(twin, ratio)]
            record = {"point_key": key, "arm": f"advr_{leg}", "is_control": is_control}
            record |= {"control_key": P.control_key(leg)}
            record |= {field: copy.deepcopy(source[field]) for field in CONTRACT}
            if is_control:
                _set_counts(record, _counts(state))
            out[key] = record
    return out


@functools.lru_cache(maxsize=None)
def _default_frontier_json():
    return json.dumps(fr.build_frontier(_forged_records(), _v4(), _v4_sha()))


def _default_frontier():
    return json.loads(_default_frontier_json())


def _keys_walk(node):
    if isinstance(node, dict):
        for key, value in node.items():
            yield key
            yield from _keys_walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from _keys_walk(value)


# =================================================================================================
# Task 1 — build_frontier through the frozen route
# =================================================================================================


def test_build_frontier_n8_learnable_n64_prereg03():
    frontier = _default_frontier()
    assert frontier["point_keys"] == list(KEYS)
    assert list(frontier["points"]) == list(KEYS)
    points = frontier["points"]
    c64 = points[P.control_key("n64")]["verdict"]
    assert c64["verdict"] is None and c64["early_return_reason"] == REFUSAL
    assert all(m in c64["reasons"][0] for m in P.COVERAGE_FLOOR_REFUSAL_MARKERS)
    unlearnable = {s: list(v) for s, v in _counts("unlearnable").items()}
    rest = [k for k in P.leg_keys("n64") if k != P.control_key("n64")]
    assert len(rest) == len(P.RATIO_GRID) - 1
    for key in rest:
        entry = points[key]["verdict"]
        assert entry["verdict"] is None and entry["early_return_reason"]
        assert entry["control_recall_counts"] == unlearnable
        assert points[key]["rule"] == "PREREG-03"
        assert P.point_verdict_string(points[key]) == P.REFUSED
    n8 = _counts("learnable")
    for key in P.leg_keys("n8"):
        entry = points[key]["verdict"]
        assert entry["verdict"] in P.V4_VERDICTS
        assert entry["control_taught_recall"] == n8["taught"][0] / n8["taught"][1]
        assert entry["control_heldout_recall"] == n8["heldout"][0] / n8["heldout"][1]
    assert P.admission(frontier)["verdict"] != "INCONCLUSIVE"
    readings = frontier["verdicts"]["control_readings"]
    assert readings["advr_n64"]["recall_counts"] == unlearnable
    assert (
        readings["advr_n64"]["unlearnable"] is True and readings["advr_n8"]["unlearnable"] is False
    )
    assert set(frontier["verdicts"]["leg_refusals"]) == {"advr_n64"}


def test_build_route_spy_both_legs_learnable(monkeypatch):
    real = phase25_verdict.curve_verdicts
    seen = []

    def spy(records, arm, capacity, *, control_readings_by_arm):
        seen.append((records, arm, capacity, control_readings_by_arm))
        return real(records, arm, capacity, control_readings_by_arm=control_readings_by_arm)

    monkeypatch.setattr(phase25_verdict, "curve_verdicts", spy)
    records = _forged_records(n8="learnable", n64="learnable")
    frontier = fr.build_frontier(records, _v4(), _v4_sha())
    assert [len(call[0]) for call in seen] == [len(P.RATIO_GRID)] * len(P.LEGS)
    for records_seen, arm, capacity, by_twin in seen:
        assert set(by_twin) == set(phase25_verdict.ARM_LEGS[arm])
        assert f"n{capacity}" in P.LEGS
        for leg in P.LEGS:
            control = records[P.control_key(leg)]
            got = by_twin[_twin(leg)]
            assert got["adapter_on"] == control["condition_c"]["point_dialogue_ppl_on"]
            assert got["adapter_off"] == control["condition_c"]["point_dialogue_ppl_off"]
            t, h = control["taught_recall"], control["heldout_recall"]
            assert got["taught_recall"] == t["numerator"] / t["denominator"]
            assert got["heldout_recall"] == h["numerator"] / h["denominator"]
    assert all(frontier["points"][k]["verdict"]["verdict"] in P.V4_VERDICTS for k in KEYS)
    assert frontier["verdicts"]["leg_refusals"] == {}


def test_route_structural_systemexit_propagates(monkeypatch):
    def structural(*args, **kwargs):
        raise SystemExit("structural")

    monkeypatch.setattr(phase25_verdict, "curve_verdicts", structural)
    with pytest.raises(SystemExit, match="NOT the coverage route's floor refusal: structural$"):
        fr.build_frontier(_forged_records(), _v4(), _v4_sha())


def test_build_refuses_malformed_prereg_record_sets():
    records = _forged_records()
    eleven = dict(records)
    eleven.pop(KEYS[-1])
    with pytest.raises(SystemExit, match="12"):
        fr.build_frontier(eleven, _v4(), _v4_sha())
    # A PREREG-03 record on a learnable leg.
    learnable = dict(records)
    stray = P.leg_keys("n8")[1]
    learnable[stray] = records[P.leg_keys("n64")[1]] | {"point_key": stray}
    with pytest.raises(SystemExit, match="PREREG-03"):
        fr.build_frontier(learnable, _v4(), _v4_sha())
    # A PREREG-03 record whose control counts differ from the control's.
    other = dict(records)
    key = P.leg_keys("n64")[2]
    other[key] = P.refused_record(key, taught=(0, 1008), heldout=(0, 648), recipe=_recipe("n64"))
    with pytest.raises(SystemExit, match="control_recall_counts"):
        fr.build_frontier(other, _v4(), _v4_sha())


def test_route_no_promotion_and_replication_is_false():
    frontier = _default_frontier()
    assert "promotion" not in set(_keys_walk(frontier))
    routed = [frontier["points"][k]["verdict"] for k in KEYS if "rule" not in frontier["points"][k]]
    assert routed, "no routed entry: the check is vacuous"
    for entry in routed:
        assert entry["replicated_at_second_seed"] is False
        assert entry["replicated_at_second_seed"] is fr.phase25_promotion.REPLICATED_AT_SECOND_SEED
    assert frontier["verdicts"]["replicated_at_second_seed"] is False


def test_tallies_rederive_and_a_planted_mismatch_is_read():
    frontier = _default_frontier()
    strings = {k: P.point_verdict_string(frontier["points"][k]) for k in KEYS}
    assert frontier["verdicts"]["tallies"] == P._tally(strings.values())
    by_leg = {}
    for k in KEYS:
        by_leg.setdefault(P._frontier_leg(k), []).append(strings[k])
    assert frontier["verdicts"]["tallies_by_leg"] == {g: P._tally(v) for g, v in by_leg.items()}
    assert P.admission(frontier)["verdict"] != "INCONCLUSIVE"
    frontier["verdicts"]["tallies"][P.REFUSED] += 1
    assert P.admission(frontier)["verdict"] == "INCONCLUSIVE"


def test_ast_route_gates(tmp_path):
    source = MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert _gate_retype_failures(source, mitigation_gate.F_Y) == []
    planted = _planted(tmp_path, source, source + f"\n_X = {mitigation_gate.F_Y!r}\n", "fy.py")
    assert _gate_retype_failures(planted, mitigation_gate.F_Y), "the F_Y guard is blind"
    calls = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "curve_verdicts"
    ]
    assert calls, "the frozen route is never called"
    assert _wr05_failures(source) == []
    carrier = _planted(
        tmp_path, source, source + "\n_X = phase25_promotion.control_readings\n", "wr05.py"
    )
    assert _wr05_failures(carrier), "the WR-05 guard is blind"
    replaces = [
        n.lineno
        for n in ast.walk(tree)
        if isinstance(n, ast.Attribute)
        and n.attr == "replace"
        and isinstance(n.value, ast.Name)
        and n.value.id == "os"
    ]
    assert replaces == []
    offenders, message = _git_surface_failure(MODULE, READ_ONLY_GIT)
    assert offenders == [], message
    used = {row[0] for row in _git_argv_subcommands(MODULE)}
    assert not used & {"add", "commit"}  # D-16: the emitter never commits


def test_ast_module_is_torch_free_at_import():
    code = (
        "import sys; sys.path.insert(0, 'scripts'); sys.path.insert(0, 'src'); "
        "import phase32_frontier; assert 'torch' not in sys.modules"
    )
    subprocess.run([sys.executable, "-c", code], cwd=_ROOT, check=True)


# =================================================================================================
# Task 2 — condition_c_vs_v4, the statement templates, write-once emit, v4 bytes, recompute, CLI
# =================================================================================================

C_FIELDS = (
    "point_dialogue_ppl_on",
    "point_dialogue_ppl_off",
    "point_retention_ppl",
    "control_gap",
    "gap_noise_floor",
    "retention_noise_floor",
)


def _block():
    return _default_frontier()["verdicts"]["condition_c_vs_v4"]


def test_condition_c_vs_v4_rows_against_the_committed_v4_frontier():
    frontier, v4 = _default_frontier(), _v4()
    block = frontier["verdicts"]["condition_c_vs_v4"]
    rows = block["rows"]
    expected = [(leg, ratio) for leg in P.LEGS for ratio in P.RATIO_GRID]
    assert [(r["v5_key"], r["v4_key"], r["ratio"]) for r in rows] == [
        (P.point_key(f"advr_{leg}", ratio), phase25_record.point_key(_twin(leg), ratio), ratio)
        for leg, ratio in expected
    ]
    for row in rows:
        assert row["control_self_referential_dialogue"] is (row["ratio"] == P.RATIO_GRID[0])
        # cleared_abc is handed the verdict ENTRY, never the point dict.
        assert (
            row["v5"]["cleared_c"] == P.cleared_abc(frontier["points"][row["v5_key"]]["verdict"])[2]
        )
        assert row["v4"]["cleared_c"] == P.cleared_abc(v4["points"][row["v4_key"]]["verdict"])[2]
        assert row["v5"]["verdict"] == P.point_verdict_string(frontier["points"][row["v5_key"]])
        source = v4["points"][row["v4_key"]]
        assert row["v4"]["condition_c"] == {f: source["condition_c"][f] for f in C_FIELDS}
        assert row["v4"]["verdict"] == P.point_verdict_string(source)
    n8 = [r for r in rows if r["v5_key"] in P.leg_keys("n8")]
    n64 = [r for r in rows if r["v5_key"] in P.leg_keys("n64")]
    for row in n8:
        assert row["v4"]["cleared_c"] is False and row["v4"]["verdict"] == "INCONCLUSIVE"
        assert row["v4"]["quoted_reasons"]
        assert all(r.startswith("(c)") for r in row["v4"]["quoted_reasons"])
        assert row["v5"]["state"] == "measured"
    refusal = v4["verdicts"]["leg_refusals"]["adv_n64"]
    for row in n64:
        reasons = v4["points"][row["v4_key"]]["verdict"]["reasons"]
        assert row["v4"]["cleared_c"] is None
        assert row["v4"]["label"] == "(c) measured, not evaluated"
        assert row["v4"]["quoted_reasons"] == [reasons[0]] == [refusal]
    assert n64[0]["v5"]["state"] == "refused_by_route"
    assert {r["v5"]["state"] for r in n64[1:]} == {"refused_prereg03"}
    for row in n64[1:]:
        assert row["v5"]["cleared_c"] is None
        assert row["v5"]["control_recall_counts"] == {
            s: list(v) for s, v in _counts("unlearnable").items()
        }
    assert block["v4_source"] == {"path": fr.V4_FRONTIER_PATH, "sha256": _v4_sha()}


def test_condition_c_vs_v4_cleared_abc_on_a_point_dict_raises():
    point = _v4()["points"][phase25_record.point_key("adv_n8", P.RATIO_GRID[1])]
    with pytest.raises(KeyError, match="point_extraction_successes"):
        P.cleared_abc(point)


def test_condition_c_vs_v4_leg_state_branches():
    one_route = ["refused_by_route"] + ["refused_prereg03"] * (len(P.RATIO_GRID) - 1)
    assert fr.v5_leg_state(one_route) == "refused_prereg03"
    assert fr.v5_leg_state(["refused_by_route"] * len(P.RATIO_GRID)) == "refused_by_route"
    assert fr.v5_leg_state(["measured"] * len(P.RATIO_GRID)) == "measured"
    mixed = ["measured", "refused_by_route"] * (len(P.RATIO_GRID) // 2)
    assert fr.v5_leg_state(mixed) == "measured"
    assert fr.v4_leg_state([False, True, False, False, True, False]) == "evaluated"
    assert fr.v4_leg_state([None] * len(P.RATIO_GRID)) == "not_evaluated"
    with pytest.raises(SystemExit, match="mixed"):
        fr.v4_leg_state([None, False, None, None, None, None])


def test_condition_c_vs_v4_summary_counts():
    block, v4 = _block(), _v4()
    rows = block["rows"]
    for leg in P.LEGS:
        summary = block["by_leg"][leg]
        mine = [r for r in rows if r["v5_key"] in P.leg_keys(leg)]
        assert summary["k6"] == sum(r["v5"]["cleared_c"] is True for r in mine)
        assert summary["k5"] == sum(r["v5"]["cleared_c"] is True for r in mine[1:])
        assert summary["v4_k"] == sum(r["v4"]["cleared_c"] is True for r in mine)
        assert summary["v4_n_evaluated"] == sum(r["v4"]["cleared_c"] is not None for r in mine)
        counts = v4["verdicts"]["control_readings"][_twin(leg)]["recall_counts"]
        assert [summary["v4_tk"], summary["v4_tn"]] == counts["taught"]
        assert [summary["v4_hk"], summary["v4_hn"]] == counts["heldout"]
    assert block["by_leg"]["n8"]["v5_state"] == "measured"
    assert block["by_leg"]["n8"]["v4_state"] == "evaluated"
    assert block["by_leg"]["n64"]["v5_state"] == "refused_prereg03"
    assert block["by_leg"]["n64"]["v4_state"] == "not_evaluated"


def _summary(v5_state, v4_state, k5=2, k6=3):
    return {
        "leg": "advr_n8",
        "twin": "adv_n8",
        "v5_state": v5_state,
        "v4_state": v4_state,
        "k5": k5,
        "k6": k6,
        "v4_k": 1,
        "v4_n_evaluated": 6,
        "tk": 11,
        "tn": 1008,
        "hk": 13,
        "hn": 648,
        "v4_tk": 17,
        "v4_tn": 1008,
        "v4_hk": 19,
        "v4_hn": 648,
    }


def test_statement_templates_cover_every_state():
    assert set(fr.TEMPLATES) == {(a, b) for a in fr.V5_STATES for b in fr.V4_STATES}
    assert len(fr.TEMPLATES) == len(fr.V5_STATES) * len(fr.V4_STATES)
    for v5_state, v4_state in fr.TEMPLATES:
        s = _summary(v5_state, v4_state)
        text = fr.statement({leg: dict(s, leg=f"advr_{leg}") for leg in P.LEGS})
        assert text.startswith("At advr_n8, ")
        if v5_state == "measured":
            assert "self-reference" in text
        if v5_state in ("refused_prereg03", "refused_by_route"):
            assert "taught 11/1008" in text and "held-out 13/648" in text
        if v5_state == "refused_prereg03":
            assert "PREREG-03" in text and "not re-tuned" in text
        if v4_state == "evaluated":
            assert "at 1 of 6" in text
        else:
            assert "taught 17/1008" in text and "held-out 19/648" in text
            assert "measured but not evaluated" in text


def test_statement_measured_k5_leads_k6_for_every_k5():
    for k5 in range(len(P.RATIO_GRID)):
        for v4_state in fr.V4_STATES:
            s = _summary("measured", v4_state, k5=k5, k6=k5 + 1)
            text = fr.TEMPLATES[("measured", v4_state)].format(**s)
            first, second = f"{k5} of 5 non-control ratios", f"{k5 + 1} of 6 counting"
            assert text.index(first) < text.index(second)
            assert "ratio-0 control" in text and "self-reference" in text


def test_statement_is_the_table_joined_on_the_forged_frontier():
    block = _block()
    by_leg = block["by_leg"]
    expected = " ".join(
        fr.TEMPLATES[(by_leg[leg]["v5_state"], by_leg[leg]["v4_state"])].format(
            **fr.statement_fields(by_leg[leg])
        )
        for leg in P.LEGS
    )
    assert block["statement"] == fr.statement(by_leg) == expected
    v4_n64 = _v4()["verdicts"]["control_readings"]["adv_n64"]["recall_counts"]
    tk, tn = v4_n64["taught"]
    hk, hn = v4_n64["heldout"]
    assert f"taught {tk}/{tn}, held-out {hk}/{hn}" in block["statement"]
    assert "not re-tuned" in block["statement"]
    # D-18 precision: the v4.0 side names its failing recall, derived from the committed counts.
    failed = [
        f"the {n} recall {k}/{d}"
        for n, k, d in (("taught", tk, tn), ("held-out", hk, hn))
        if not 0.0 < P.F_Y * (k / d) <= 1.0
    ]
    assert failed and all(f in block["statement"] for f in failed)


_INEQ = "0 < F_Y × recall <= 1"


def _n64_summary(tk, hk, v4_tk, v4_hk):
    return dict(
        _summary("refused_prereg03", "not_evaluated"),
        leg="advr_n64",
        twin="adv_n64",
        tk=tk,
        hk=hk,
        v4_tk=v4_tk,
        v4_hk=v4_hk,
    )


def test_statement_names_the_failing_recall_per_side():
    """The developer's D-16 ruling: v5 n64 taught 0/1008 fails, held-out 1/648 passes;
    v4 n64 held-out 0/648 fails, taught 1/1008 passes."""
    s = _n64_summary(tk=0, hk=1, v4_tk=1, v4_hk=0)
    text = fr.TEMPLATES[("refused_prereg03", "not_evaluated")].format(**fr.statement_fields(s))
    v5, v4 = text.split("; in v4.0")
    assert "the taught recall 0/1008 violates and the held-out recall 1/648 satisfies" in v5
    assert _INEQ in v5 and f"F_Y = {P.F_Y}" in v5
    assert "the held-out recall 0/648 violates and the taught recall 1/1008 satisfies" in v4
    assert _INEQ in v4
    assert "outside (0,1]" not in text


def test_statement_floor_words_are_derived_not_typed():
    """Swapping the counts swaps the words: nothing about which recall failed is typed."""
    s = _n64_summary(tk=1, hk=0, v4_tk=0, v4_hk=1)
    text = fr.TEMPLATES[("refused_prereg03", "not_evaluated")].format(**fr.statement_fields(s))
    v5, v4 = text.split("; in v4.0")
    assert "the held-out recall 0/648 violates and the taught recall 1/1008 satisfies" in v5
    assert "the taught recall 0/1008 violates and the held-out recall 1/648 satisfies" in v4


def test_recall_floors_agree_with_control_is_unlearnable():
    for tk in (0, 1, 500, 1008):
        for hk in (0, 1, 300, 648):
            floors = fr.recall_floors(tk, 1008, hk, 648)
            assert set(floors) == {"taught", "held-out"}
            failed = [name for name, ok in floors.items() if not ok]
            assert bool(failed) == P.control_is_unlearnable(tk, 1008, hk, 648)
            assert floors["taught"] == (0.0 < P.F_Y * (tk / 1008) <= 1.0)
            assert floors["held-out"] == (0.0 < P.F_Y * (hk / 648) <= 1.0)


# ----- write-once emit ----------------------------------------------------------------------


def _is_tracked(rel):
    return rel in _git("ls-files", rel).split()


def _point_paths():
    return [P.point_record_path(k) for k in KEYS]


def test_emit_write_once_refuses_an_existing_target_first(tmp_path, clean_tree):
    out = tmp_path / "frontier.json"
    out.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit, match="REFUSING to overwrite"):
        fr.emit(out_path=out)
    assert clean_tree == []
    assert out.read_text(encoding="utf-8") == "{}"


def _commit(root, rel, data, message):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    subprocess.run(["git", "-C", str(root), "add", rel], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", message], check=True)


def test_emit_write_once_scratch_repo(tmp_path, monkeypatch, clean_tree):
    root = _scratch_repo(tmp_path)
    monkeypatch.setattr(fr, "_GIT_ROOT", root)
    monkeypatch.setattr(phase30_points, "_ROOT", root)
    _commit(root, phase30_points.CALIBRATION_PATH, b"{}", "calibration")
    _commit(root, fr.BUDGET_PATH, b"{}", "budget")
    _commit(root, fr.V4_FRONTIER_PATH, _v4_bytes(), "v4 frontier")
    records = _forged_records()
    for key in KEYS[:-1]:
        _commit(root, P.point_record_path(key), json.dumps(records[key]).encode(), key)
    out = tmp_path / "frontier.json"
    with pytest.raises(SystemExit, match="UNTRACKED"):
        fr.emit(out_path=out)
    assert not out.exists()
    (call,) = clean_tree
    assert call["cwd"] == root
    assert call["pathspec"] == ("scripts", "src", "results", f":(exclude){fr.FRONTIER_PATH}")
    _commit(root, P.point_record_path(KEYS[-1]), json.dumps(records[KEYS[-1]]).encode(), "last")
    written = fr.emit(out_path=out)
    assert json.loads(out.read_text(encoding="utf-8")) == json.loads(json.dumps(written))
    assert not (root / fr.FRONTIER_PATH).exists()
    assert set(written["sources"]) == {*_point_paths(), fr.V4_FRONTIER_PATH, fr.BUDGET_PATH}
    assert written["sources"][fr.V4_FRONTIER_PATH] == _v4_sha()
    assert written["calibration"]["path"] == phase30_points.CALIBRATION_PATH
    assert set(written["provenance"]["module_sha256"]) == set(fr.PROVENANCE_MODULES)
    strip = {"provenance", "calibration", "sources"}
    rebuilt = json.loads(json.dumps(fr.build_frontier(records, _v4(), _v4_sha())))
    assert {k: v for k, v in written.items() if k not in strip} == rebuilt


def test_emit_write_once_real_state(tmp_path, clean_tree):
    tracked = set(_git("ls-files", "results").split())
    target = _ROOT / fr.FRONTIER_PATH
    if target.exists():  # (c) present untracked, or (d) tracked
        before = target.read_bytes()
        with pytest.raises(SystemExit, match="REFUSING to overwrite"):
            fr.emit(out_path=fr.FRONTIER_PATH)
        assert clean_tree == [] and target.read_bytes() == before
        return
    out = tmp_path / "f.json"
    if not set(_point_paths()) <= tracked:  # (a) some point record untracked
        with pytest.raises(SystemExit, match="UNTRACKED"):
            fr.emit(out_path=out)
        assert not out.exists()
    else:  # (b) all 12 tracked, frontier absent
        fr.emit(out_path=out)
        assert out.exists()
    assert not target.exists()


def test_emit_never_commits_and_the_git_surface_is_read_only():
    used = {row[0] for row in _git_argv_subcommands(MODULE)}
    assert {"ls-files", "show", "log", "merge-base"} <= used  # non-vacuous
    assert used <= READ_ONLY_GIT
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    emit = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "emit")
    strings = {n.value for n in ast.walk(emit) if isinstance(n, ast.Constant)}
    assert not strings & {"add", "commit", "push"}


# ----- v4 bytes, committed recompute, ancestry ---------------------------------------------


def test_v4_bytes_unchanged_since_the_v4_tag():
    argv = [
        "git",
        "diff",
        "--quiet",
        "v4.0",
        "HEAD",
        "--",
        "results",
        ":(exclude)results/phase24_token_budget.json",
        ":(exclude)results/phase3*",
    ]
    assert subprocess.run(argv, cwd=_ROOT).returncode == 0
    # NATURAL RED: phase24_token_budget.json was re-emitted in Phase 30, so the check sees changes.
    red = ["git", "diff", "--quiet", "v4.0", "HEAD", "--", "results/phase24_token_budget.json"]
    assert subprocess.run(red, cwd=_ROOT).returncode == 1


def _strip(record):
    return {k: v for k, v in record.items() if k not in ("provenance", "calibration", "sources")}


def _committed(rel):
    return subprocess.run(
        ["git", "show", f"HEAD:{rel}"], cwd=_ROOT, capture_output=True, check=True
    ).stdout


def test_recompute_committed_frontier_both_states():
    import hashlib

    if _is_tracked(fr.FRONTIER_PATH):
        records = {k: json.loads(_committed(P.point_record_path(k))) for k in KEYS}
        rebuilt = json.loads(json.dumps(fr.build_frontier(records, _v4(), _v4_sha())))
        committed = json.loads(_committed(fr.FRONTIER_PATH))
        assert _strip(rebuilt) == _strip(committed)
        sources = committed["sources"]
        assert set(sources) == {*_point_paths(), fr.V4_FRONTIER_PATH, fr.BUDGET_PATH}
        for rel, digest in sources.items():
            assert digest == hashlib.sha256(_committed(rel)).hexdigest(), rel
        return
    first = json.loads(json.dumps(fr.build_frontier(_forged_records(), _v4(), _v4_sha())))
    second = json.loads(json.dumps(fr.build_frontier(_forged_records(), _v4(), _v4_sha())))
    assert first == second
    assert not {"provenance", "calibration", "sources"} & set(first)


def test_ancestry_frontier_follows_its_inputs():
    if not _is_tracked(fr.FRONTIER_PATH):
        assert _git("ls-files", "results/phase32_frontier*").split() == []
        return
    for rel in [*_point_paths(), fr.BUDGET_PATH]:
        _assert_frozen_before(rel, [fr.FRONTIER_PATH])
    # NATURAL RED: the calibration was added before the budget existed.
    with pytest.raises(subprocess.CalledProcessError):
        _assert_frozen_before(fr.BUDGET_PATH, [phase30_points.CALIBRATION_PATH])


# ----- CLI -----------------------------------------------------------------------------------


def test_cli_main_dispatches_emit(monkeypatch):
    import inspect

    calls = []
    real = inspect.signature(fr.emit)

    def recorder(*args, **kwargs):
        real.bind(*args, **kwargs)
        calls.append(kwargs)

    monkeypatch.setattr(fr, "emit", recorder)
    assert fr.main(["emit"]) == 0
    assert fr.main(["emit", "--out", "/tmp/x.json"]) == 0
    assert calls == [{"out_path": fr.FRONTIER_PATH}, {"out_path": "/tmp/x.json"}]
